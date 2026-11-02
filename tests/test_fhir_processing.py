import pandas as pd
from fhir_processing import validate_measurements


def test_validate_heart_rate():

    # Arrange
    df = pd.DataFrame({
        "numeric_value": [75, -20, 350]
    })

    # Act
    result = validate_measurements(
        df,
        min_value=0,
        max_value=300
    )

    # Assert
    assert result["is_valid"].tolist() == [True, False, False]

def test_validate_missing_values():

    # Arrange
    df = pd.DataFrame({
        "numeric_value": [80, None, 120]
    })

    # Act
    result = validate_measurements(
        df,
        min_value=0,
        max_value=300
    )

    # Assert
    assert result["is_valid"].tolist() == [True, False, True]