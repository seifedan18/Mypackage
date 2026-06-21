"""Automated data-validation tests for the Maji Ndogo data pipeline.

These ``pytest`` tests read the sampled CSV files that the notebook exports
(``sampled_field_df.csv`` and ``sampled_weather_df.csv``) and check that the
processed data matches what we expect: the correct shapes, the correct
columns, non-negative elevations, valid crop types and non-negative rainfall.
"""

import pytest
import pandas as pd


@pytest.fixture
def field_df():
    return pd.read_csv("sampled_field_df.csv")


@pytest.fixture
def weather_df():
    return pd.read_csv("sampled_weather_df.csv")


def test_read_weather_DataFrame_shape(weather_df):
    """The processed weather DataFrame should have 1843 rows and 4 columns."""
    assert weather_df.shape == (1843, 4)


def test_read_field_DataFrame_shape(field_df):
    """The processed field DataFrame should have 5654 rows and 19 columns."""
    assert field_df.shape == (5654, 19)


def test_weather_DataFrame_columns(weather_df):
    """The weather DataFrame should contain exactly the expected columns."""
    expected_columns = ['Weather_station_ID', 'Message', 'Measurement', 'Value']
    assert list(weather_df.columns) == expected_columns


def test_field_DataFrame_columns(field_df):
    """The field DataFrame should contain exactly the expected columns."""
    expected_columns = [
        'Field_ID', 'Elevation', 'Latitude', 'Longitude', 'Location', 'Slope',
        'Rainfall', 'Min_temperature_C', 'Max_temperature_C', 'Ave_temps',
        'Soil_fertility', 'Soil_type', 'pH', 'Pollution_level', 'Plot_size',
        'Annual_yield', 'Crop_type', 'Standard_yield', 'Weather_station'
    ]
    assert list(field_df.columns) == expected_columns


def test_field_DataFrame_non_negative_elevation(field_df):
    """Elevation values should all be non-negative after the corrections."""
    assert (field_df['Elevation'] >= 0).all()


def test_crop_types_are_valid(field_df):
    """Crop types should all be valid (typos and stray spaces removed)."""
    valid_crop_types = ['cassava', 'wheat', 'tea', 'potato', 'banana', 'coffee', 'rice', 'maize']
    assert field_df['Crop_type'].isin(valid_crop_types).all()


def test_positive_rainfall_values(field_df):
    """Rainfall values should all be non-negative."""
    assert (field_df['Rainfall'] >= 0).all()
