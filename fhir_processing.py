import json
import pandas as pd

def build_patient_lookup(bundle):
  patient_lookup = {}

  for entry in bundle.get("entry", []):
      resource = entry.get("resource", {})

      if resource.get("resourceType") == "Patient":
          patient_id = resource.get("id")
          full_url = entry.get("fullUrl")

          if full_url and patient_id:
              patient_lookup[full_url] = patient_id

          if patient_id:
              patient_lookup[f"Patient/{patient_id}"] = patient_id
  # Wir nehmen nur Patienten in unser Lookup auf, für die eine tatsächliche Patient.id vorhanden ist.
  return patient_lookup


def extract_patient_info(patient):

    # 1. Patient ID extrahieren
    patient_id = patient.get("id")

    # 2. Namen initialisieren
    full_name = None

    # 3. Zuerst nach dem offiziellen Namen suchen
    for name in patient.get("name", []):
        if name.get("use") == "official":
            first_names = name.get("given", [])
            last_name = name.get("family", "")

            full_name = " ".join(first_names + [last_name]).strip()
            break

    # 4. Falls kein offizieller Name vorhanden ist:
    #    Nach einem üblichen Namen suchen
    if full_name is None:
        for name in patient.get("name", []):
            if name.get("use") == "usual":
                first_names = name.get("given", [])
                last_name = name.get("family", "")

                full_name = " ".join(first_names + [last_name]).strip()
                break

    # 5. Weitere Patienteninformationen extrahieren
    gender = patient.get("gender")
    birth_date = patient.get("birthDate")

    # 6. Vereinfachtes Dictionary zurückgeben
    return {
        "patient_id": patient_id,
        "full_name": full_name,
        "gender": gender,
        "birth_date": birth_date,
    }

def extracting_conditions(bundle, patient_lookup):
    conditions = []

    # Condition-Ressourcen extrahieren
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})

        if resource.get("resourceType") != "Condition":
            continue

        condition_id = resource.get("id")

        # Patientenreferenz auflösen
        patient_ref = resource.get("subject", {}).get("reference")
        patient_id = patient_lookup.get(patient_ref)

        # Diagnosenkodierung
        codings = resource.get("code", {}).get("coding", [])
        coding = codings[0] if codings else {}

        condition_code = coding.get("code")
        condition_system = coding.get("system")
        condition_display = coding.get("display")

        # Klinischer Status
        status_codings = resource.get("clinicalStatus", {}).get("coding", [])
        clinical_status = (
            status_codings[0].get("code")
            if status_codings
            else None
        )

        conditions.append({
            "condition_id": condition_id,
            "patient_id": patient_id,
            "condition_code": condition_code,
            "condition_system": condition_system,
            "condition_display": condition_display,
            "clinical_status": clinical_status
        })

    return conditions

def extracting_observations(bundle, patient_lookup):
    observations = []

    #Observation-Ressourcen extrahieren
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})

        if resource.get("resourceType") != "Observation":
            continue

        observation_id = resource.get("id")

        # Patientenreferenz auflösen
        patient_ref = resource.get("subject", {}).get("reference")
        patient_id = patient_lookup.get(patient_ref)

        # Observationkodierung
        extracted_value = extract_component_value(resource)

        observation_value = extracted_value.get("value")
        observation_unit = extracted_value.get("unit")
        #observation_value_type = extracted_value.get("value_type")

        codings = resource.get("code", {}).get("coding", [])
        coding = codings[0] if codings else {}
        observation_code = coding.get("code")
        observation_system = coding.get("system")
        observation_display = coding.get("display")
        observation_datetime = resource.get("effectiveDateTime")

        # Observation Status
        observation_status = resource.get("status")

        # Mögliche Components
        if resource.get("component"):
          components = extract_components(resource)

          for component in components:
              observations.append({
                  "observation_id": observation_id,
                  "patient_id": patient_id,
                  "observation_code": component.get("code"),
                  "observation_system": component.get("system"),
                  "observation_display": component.get("display"),
                  "observation_value": component.get("value"),
                  "observation_unit": component.get("unit"),
                  "observation_datetime": observation_datetime,
                  "observation_status": observation_status,
                  "observation_value_type": component.get("value_type")
              })

        else:
          observations.append({
          "observation_id": observation_id,
          "patient_id": patient_id,
          "observation_code": observation_code,
          "observation_system": observation_system,
          "observation_display": observation_display,
          "observation_value": observation_value,
          "observation_unit": observation_unit,
          "observation_datetime": observation_datetime,
          "observation_status": observation_status,
          "observation_value_type": get_value_type(resource)
          })

    return observations

def get_value_type(component):

    possible_types = [
        "valueQuantity",
        "valueCodeableConcept",
        "valueString",
        "valueBoolean"
    ]

    for value_type in possible_types:

        if value_type in component:
            return value_type

    return None

def get_patient_data(patient_id, df_patients, df_conditions, df_observations):
    patient_data = df_patients[df_patients["patient_id"] == patient_id]

    if patient_data.empty:
      raise ValueError("Patient not found")

    patient_conditions = df_conditions[df_conditions["patient_id"] == patient_id]
    patient_observations = df_observations[df_observations["patient_id"] == patient_id]

    return patient_data, patient_conditions, patient_observations

def clean_observations(df):
    df = df.copy()

    # 1. observation_datetime konvertieren
    df["observation_datetime"] = pd.to_datetime(
    df["observation_datetime"],
    errors="coerce",
    utc=True
    )

    # 2. numeric_value erstellen
    df["numeric_value"] = pd.to_numeric(
    df["observation_value"].where(
        df["observation_value_type"] == "valueQuantity"
    ),
    errors="coerce"
    )

    # 3. categorical_value erstellen
    df["categorical_value"] = (
    df["observation_value"].where(
        df["observation_value_type"].isin(
            ["valueCodeableConcept", "valueString"]
        )
    )
    )

    # 4. observation_row_id erstellen
    df["observation_row_id"] = range(
    1,
    len(df) + 1
    )

    return df

def extract_component_value(component):

    value_type = get_value_type(component)

    if value_type == "valueQuantity":
        value_quantity = component.get("valueQuantity") or {}

        value = value_quantity.get("value")
        unit = value_quantity.get("unit")

    elif value_type == "valueCodeableConcept":
        categorical = extract_categorical_value(component)

        value = categorical.get("display")
        unit = None

    elif value_type == "valueString":
        value = component.get("valueString")
        unit = None

    elif value_type == "valueBoolean":
        value = component.get("valueBoolean")
        unit = None

    else:
        value = None
        unit = None

    return {
        "value_type": value_type,
        "value": value,
        "unit": unit
    }

def extract_categorical_value(component):
    value_codeable_concept = component.get("valueCodeableConcept") or {}

    coding_list = value_codeable_concept.get("coding", [])
    coding = coding_list[0] if coding_list else {}

    return {
        "code": coding.get("code"),
        "system": coding.get("system"),
        "display": coding.get("display")
    }

def extract_components(resource):
    components = []

    for component in resource.get("component", []):
        component_coding = component.get("code", {}).get("coding", [])
        coding = component_coding[0] if component_coding else {}

        extracted_value = extract_component_value(component)

        components.append({
            "code": coding.get("code"),
            "system": coding.get("system"),
            "display": coding.get("display"),
            "value": extracted_value.get("value"),
            "unit": extracted_value.get("unit"),
            "value_type": extracted_value.get("value_type")
        })

    return components

def process_fhir_bundle(bundle):
    patient_lookup = build_patient_lookup(bundle)

    patient_resources = [
        entry["resource"]
        for entry in bundle.get("entry", [])
        if entry.get("resource", {}).get("resourceType") == "Patient"
    ]

    patients = [extract_patient_info(p) for p in patient_resources]
    conditions = extracting_conditions(bundle, patient_lookup)
    observations = extracting_observations(bundle, patient_lookup)

    df_patients = pd.DataFrame(patients)
    df_conditions = pd.DataFrame(conditions)
    df_observations = pd.DataFrame(observations)

    #df_observations mit clean_observations() bereinigen
    df_observations = clean_observations(df_observations)

    #Alle drei DataFrames zurückgeben
    return df_patients, df_conditions, df_observations

def validate_measurements(df, min_value, max_value):
    df_validated = df.copy()

    df_validated["is_valid"] = (
        (df_validated["numeric_value"] >= min_value)
        &
        (df_validated["numeric_value"] <= max_value)
    )

    return df_validated

if __name__ == "__main__":
    with open("data/patient_file_1.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    print("FHIR Bundle successfully loaded!")
    print("Number of entries:", len(data.get("entry", [])))

    df_patients, df_conditions, df_observations = process_fhir_bundle(data)

    print("Patients:", df_patients.shape)
    print("Conditions:", df_conditions.shape)
    print("Observations:", df_observations.shape)

    print(df_observations["observation_value_type"].value_counts(dropna=False))
    print("Numeric values:", df_observations["numeric_value"].notna().sum())
    assert len(df_observations) == 231
    assert df_observations["observation_row_id"].is_unique
    assert df_observations["numeric_value"].notna().sum() == 131