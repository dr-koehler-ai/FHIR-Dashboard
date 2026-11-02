# FHIR Clinical Patient Dashboard

## Project Overview

The **FHIR Clinical Patient Dashboard** is a Python-based application designed to demonstrate how standardized healthcare data can be retrieved, processed, and visualized using HL7 FHIR R4.

The dashboard integrates both locally generated synthetic patient data and a public FHIR REST API to display patient demographics, clinical conditions, and time-ordered observations commonly represented in electronic health record (EHR) systems.

By linking clinical resources through patient references, the application demonstrates how FHIR supports healthcare interoperability and structured data integration.

Additionally, the dashboard implements parameter-specific plausibility checks and measurement-unit validation to identify potentially unreliable observations and support safer clinical data visualization.

## Key Features

- **Dual Data Source Integration:** Supports locally generated synthetic FHIR R4 data and retrieval of patient records through a public FHIR REST API.
- **Patient-Centric Data Integration:** Links patient demographics, clinical conditions, and observations using FHIR patient references.
- **Interactive Patient Selection:** Enables users to select individual patients and explore their available clinical records.
- **Clinical Data Visualization:** Provides interactive Plotly charts with measurement selection, chronological display, and date-range filtering.
- **Data Quality and Plausibility Checks:** Applies parameter-specific plausibility thresholds and detects missing or inconsistent measurement units before visualization.

## Tech Stack

| Technology | Purpose |
|---|---|
| **Python** | Core application logic and FHIR data processing |
| **HL7 FHIR R4** | Standardized representation and exchange of healthcare data |
| **Streamlit** | Interactive web application and user interface |
| **Pandas** | Data extraction, transformation, filtering, and validation |
| **Plotly** | Interactive visualization of clinical observations |
| **Requests** | HTTP communication with the public FHIR REST API |
| **Pytest** | Automated unit testing of data validation functions |

## Architecture

The application follows a modular architecture, separating data retrieval, processing, validation, and visualization.

**Data Sources**
- Local synthetic patient records generated using Synthea (FHIR R4 JSON)
- Public HAPI FHIR R4 REST API

**Data Processing**

FHIR resources are extracted and transformed into structured Pandas DataFrames.

The application processes three main FHIR resource types:

- `Patient` — demographic and identifying patient information
- `Condition` — documented diagnoses and clinical conditions
- `Observation` — clinical measurements and laboratory observations

Patient references are used to associate clinical resources with the corresponding patient records.

**Application Components**

| File | Responsibility |
|---|---|
| `app.py` | Streamlit user interface, patient selection, filtering, and visualization |
| `fhir_api.py` | Retrieval of FHIR resources through REST API requests |
| `fhir_processing.py` | FHIR resource extraction, transformation, and data validation |
| `data/patient_file_1.json` | Local synthetic FHIR data |
| `tests/test_fhir_processing.py` | Automated unit tests |

**Data Flow**

1. Retrieve FHIR resources from local JSON files or the public REST API.
2. Extract and transform Patient, Condition, and Observation resources.
3. Associate clinical resources using patient references.
4. Apply data quality and plausibility checks.
5. Display patient-specific information and interactive visualizations.

## Clinical Data Validation

The dashboard implements basic data quality and plausibility checks to identify potentially unreliable measurements.

**Implemented Checks**

- Detection of missing numerical measurement values
- Parameter-specific plausibility thresholds
- Identification of missing or inconsistent measurement units
- Classification of measurements according to defined validation rules

**Important:** Passing a plausibility check does not establish that a measurement is clinically normal or medically appropriate. The dashboard is an educational prototype and is not intended for clinical decision-making.

## Installation and Usage

### Prerequisites

- Python 3.10 or newer
- Internet connection for accessing the public FHIR REST API

### 1. Clone the Repository

```bash
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>.git
cd <YOUR_REPOSITORY>
```

Replace the placeholders with your GitHub username and repository name.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment:

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

To run the automated tests, install Pytest:

```bash
python -m pip install pytest
```

### 4. Launch the Dashboard

```bash
streamlit run app.py
```

Streamlit will display a local URL, typically:

`http://localhost:8501`

### 5. Explore the Application

Select one of the available data sources:

- **Local Synthea Data:** Explore synthetic patient records stored in the project.
- **FHIR REST API:** Retrieve available patient records and associated clinical resources from the public HAPI FHIR server.

Select a patient to explore demographic information, clinical conditions, and observations.

Use the available measurement filters and interactive charts to examine clinical data over time.

## Testing

Automated unit tests are implemented using Pytest.

The current test suite covers:

1. **Heart Rate Plausibility Validation:** Confirms that values within configured boundaries are accepted and out-of-range values are flagged.
2. **Missing Value Handling:** Confirms that missing numerical measurements are classified as invalid.

Run the tests from the project root directory:

```bash
python -m pytest -v
```

Both implemented tests passed during local development.

The tests focus on selected validation functions and do not constitute comprehensive clinical or integration testing.

## Limitations and Future Improvements

### Current Limitations

- **Public Test Server:** The HAPI FHIR server contains publicly accessible test data. Availability, completeness, and consistency may vary.
- **Limited API Retrieval:** The current implementation requests five patients and up to five observations and five conditions per selected patient. FHIR pagination is not yet implemented.
- **Basic Validation:** Data quality checks use predefined rules and do not replace comprehensive clinical validation.
- **Limited Test Coverage:** Automated tests currently cover selected measurement validation scenarios.
- **No Production EHR Integration:** The application does not connect to a live clinical production environment.

### Potential Future Improvements

- Implement FHIR pagination to retrieve larger datasets.
- Add standardized terminology support, including LOINC and SNOMED CT.
- Expand automated unit and integration testing.
- Improve handling of different FHIR Observation value types.
- Introduce additional data quality metrics and validation reports.
- Explore integration with clinical analytics and machine learning workflows.

## Data Privacy and Intended Use

This project is intended exclusively for my own educational purposes and technical demonstration.

The local dataset contains synthetic patient records generated with Synthea. The API integration uses a public FHIR test server. No real patient-identifiable information should be uploaded to the application or submitted to the public test server.

**This dashboard is not a certified medical device and must not be used for diagnosis, treatment decisions, or direct patient care.**
