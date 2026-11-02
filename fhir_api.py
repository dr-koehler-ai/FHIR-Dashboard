import requests
from fhir_processing import process_fhir_bundle

BASE_URL = "https://hapi.fhir.org/baseR4"

def fetch_fhir_resources(resource, patient_id):

    response = requests.get(
        f"{BASE_URL}/{resource}",
        params={
            "patient": patient_id,
            "_count": 5
        },
        headers={"Accept": "application/fhir+json"},
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    return data

def load_api_data():
    response = requests.get(
        f"{BASE_URL}/Patient",
        params={"_count": 5},
        headers={"Accept": "application/fhir+json"},
        timeout=15
    )

    response.raise_for_status()
    data = response.json()

    patient_entries = data.get("entry", [])

    patient_ids = []

    for entry in patient_entries:
        patient = entry.get("resource", {})
        patient_id = patient.get("id")

        if patient_id:
            patient_ids.append(patient_id)

    all_observation_entries = []
    all_condition_entries = []

    for patient_id in patient_ids:

        observations_data = fetch_fhir_resources(
            "Observation",
            patient_id
        )

        conditions_data = fetch_fhir_resources(
            "Condition",
            patient_id
        )

        all_observation_entries.extend(
            observations_data.get("entry", [])
        )

        all_condition_entries.extend(
            conditions_data.get("entry", [])
        )

    all_entries = patient_entries + all_observation_entries + all_condition_entries
    combined_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": all_entries
    }

    df_patients, df_conditions, df_observations = process_fhir_bundle(combined_bundle)

    print("Patients:", len(df_patients))
    print("Conditions:", len(df_conditions))
    print("Observations:", len(df_observations))
    print(df_observations["patient_id"].unique())
    print(df_observations.groupby("patient_id").size())

    return df_patients, df_conditions, df_observations