import streamlit as st
import json
import plotly.express as px
import pandas as pd
from fhir_processing import (
    process_fhir_bundle,
    get_patient_data,
    validate_measurements
)
from fhir_api import load_api_data

VALIDATION_RULES = {
    "8867-4": {"min_value": 0, "max_value": 300},
    "2708-6": {"min_value": 0, "max_value": 100}
}

@st.cache_data(ttl=600)
def load_cached_api_data():
    return load_api_data()

def load_fhir_data():
    print("FHIR ETL pipeline is running...")

    with open("data/patient_file_1.json", "r", encoding="utf-8") as file:
        bundle = json.load(file)

    return process_fhir_bundle(bundle)


st.title("FHIR Clinical Patient Dashboard")
st.write("My first clinical Streamlit application!")

data_source = st.selectbox(
    "Select data source:",
    options=["Local Synthea Data", "FHIR REST API"]
)

if data_source == "Local Synthea Data":
    df_patients, df_conditions, df_observations = load_fhir_data()
else:
    df_patients, df_conditions, df_observations = load_cached_api_data()

patient_ids = df_patients["patient_id"].tolist()

selected_patient_id = st.selectbox(
    "Select a patient:",
    options=patient_ids,
    format_func=lambda patient_id: df_patients.loc[
        df_patients["patient_id"] == patient_id,
        "full_name"
    ].iloc[0]
)

patient_data, patient_conditions, patient_observations = get_patient_data(
    selected_patient_id,
    df_patients,
    df_conditions,
    df_observations
)

tab1, tab2, tab3 = st.tabs([
    "Patient Overview",
    "Diagnoses",
    "Measurements"
])

diagnoses_display = patient_conditions[
    ["condition_display", "clinical_status"]
].copy()

diagnoses_display = diagnoses_display.rename(columns={
    "condition_display": "Diagnosis",
    "clinical_status": "Clinical Status"
})

with tab2:
    st.subheader("Patient Diagnoses")
    st.dataframe(diagnoses_display, hide_index=True)

with tab1:
    st.subheader("Patient Overview")
    st.write("Patient ID:", selected_patient_id)
    st.write("Patient Name:", patient_data["full_name"].iloc[0])

numeric_observations = patient_observations[
    patient_observations["numeric_value"].notna()
].copy()

measurements_display = numeric_observations[
    [
        "observation_display",
        "numeric_value",
        "observation_unit",
        "observation_datetime"
    ]
].copy()

measurements_display = measurements_display.rename(columns={
    "observation_display": "Measurement",
    "numeric_value": "Value",
    "observation_unit": "Unit",
    "observation_datetime": "Date"
})

with tab3:
    st.subheader("Laboratory and Vital Measurements")
    st.dataframe(measurements_display, hide_index=True)

# Prepare unique measurement codes and names
measurement_options = numeric_observations[
    ["observation_code", "observation_display"]
].dropna().drop_duplicates()

# Extract available LOINC codes
available_codes = measurement_options["observation_code"].unique()

with tab3:
# Select measurement by code, display readable name
    selected_code = st.selectbox(
        "Select a measurement:",
        options=available_codes,
        format_func=lambda code: (
            f"{measurement_options.loc[measurement_options['observation_code'] == code, 'observation_display'].iloc[0]} ({code})"
        )
    )

selected_measurement = measurement_options.loc[
    measurement_options["observation_code"] == selected_code,
    "observation_display"
].iloc[0]

with tab3:
    st.subheader("Selected Measurement")
    st.write("Selected measurement:", selected_measurement)

df_selected_measurement = numeric_observations[
    numeric_observations["observation_code"] == selected_code
].copy()


df_selected_measurement = df_selected_measurement.sort_values("observation_datetime")

df_selected_measurement["observation_datetime"] = pd.to_datetime(
    df_selected_measurement["observation_datetime"],
    utc=True
)

# Define available date range
min_date = df_selected_measurement["observation_datetime"].min().date()
max_date = df_selected_measurement["observation_datetime"].max().date()

# Interactive date selection
with tab3:
    selected_dates = st.date_input(
        "Select date range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# Filter measurements by selected date range
if len(selected_dates) == 2:
    start_date, end_date = selected_dates

    df_filtered = df_selected_measurement[
        (df_selected_measurement["observation_datetime"].dt.date >= start_date)
        &
        (df_selected_measurement["observation_datetime"].dt.date <= end_date)
    ].copy()
else:
    st.info("Please select a start and end date.")
    st.stop()

with tab3:
    st.write("Selected dates:", selected_dates)

no_measurement = df_filtered.empty

selected_rule = VALIDATION_RULES.get(selected_code,None)

if selected_rule is not None:
    df_validated = validate_measurements(
        df_filtered,
        min_value=selected_rule["min_value"],
        max_value=selected_rule["max_value"]
    )
else:
    with tab3:
        st.info(
        "No parameter-specific validation rule available. "
        "Measurements have not been checked for clinical plausibility."
        )
    df_validated = df_filtered.copy()
    df_validated["is_valid"] = pd.NA 

if selected_rule is not None:
    df_plot = df_validated[
        df_validated["is_valid"] == True
    ].copy()
else:
    df_plot = df_validated.copy()

multiple_units = (
    df_plot["observation_unit"].dropna().nunique() > 1
)

missing_units = df_plot["observation_unit"].isna().any()

unsafe_units = multiple_units or missing_units

total_measurements = len(df_validated)

excluded_measurements = len(df_validated) - len(df_plot)

with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Measurements", len(df_validated))

    with col2:
        if selected_rule is not None:
            st.metric(
                "Excluded Measurements",
                len(df_validated) - len(df_plot)
            )
        else:
            st.metric("Excluded Measurements", "Not assessed")
        
with tab3:
    if no_measurement:
        st.info("No measurements available for the selected date range.")

    elif df_plot.empty:
        st.warning(
            "All measurements were excluded by the validation rules."
        )

    elif unsafe_units:
        st.warning(
            "Multiple or missing measurement units detected. "
            "The chart cannot be displayed safely."
        )

    else:
        selected_unit = df_plot["observation_unit"].iloc[0]

        fig = px.scatter(
            df_plot,
            x="observation_datetime",
            y="numeric_value",
            labels={
                "observation_datetime": "Measurement Date",
                "numeric_value": f"Value ({selected_unit})"
            },
            title=selected_measurement
        )

        fig.update_traces(
            hovertemplate=(
                "Date: %{x|%d.%m.%Y, %H:%M}"
                "<br>Value: %{y} " + str(selected_unit)
                + "<extra></extra>"
            )
        )

        st.plotly_chart(fig, use_container_width=True)

        # Hier bleiben dein fig.update_traces(...)
        # und st.plotly_chart(fig, use_container_width=True)
        # ebenfalls eingerückt.