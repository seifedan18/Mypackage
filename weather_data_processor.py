"""Weather data processing for the Maji Ndogo data pipeline.

This module defines :class:`WeatherDataProcessor`, which reads the weather
station data from a CSV on the web and extracts the numeric measurements
(rainfall, temperature and pollution level) that are buried inside the free
text ``Message`` column using regular expressions.

As with :class:`field_data_processor.FieldDataProcessor`, all settings (the
CSV URL and the regex patterns) are supplied through a ``config_params``
dictionary.
"""

import re
import numpy as np
import pandas as pd
import logging
from data_ingestion import read_from_web_CSV


class WeatherDataProcessor:
    """Read and process the weather station data into a tidy DataFrame."""

    def __init__(self, config_params, logging_level="INFO"):
        """Initialise the processor from a configuration dictionary.

        Parameters
        ----------
        config_params : dict
            Dictionary with the keys ``'weather_csv_path'`` and
            ``'regex_patterns'``.
        logging_level : str, optional
            One of ``"DEBUG"``, ``"INFO"`` or ``"NONE"``. Defaults to
            ``"INFO"``.
        """
        self.weather_station_data = config_params['weather_csv_path']
        self.patterns = config_params['regex_patterns']
        self.weather_df = None  # Initialize weather_df as None or as an empty DataFrame
        self.initialize_logging(logging_level)

    def initialize_logging(self, logging_level):
        """Set up logging for this instance of WeatherDataProcessor."""
        logger_name = __name__ + ".WeatherDataProcessor"
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False  # Prevents log messages from being propagated to the root logger

        # Set logging level
        if logging_level.upper() == "DEBUG":
            log_level = logging.DEBUG
        elif logging_level.upper() == "INFO":
            log_level = logging.INFO
        elif logging_level.upper() == "NONE":  # Option to disable logging
            self.logger.disabled = True
            return
        else:
            log_level = logging.INFO  # Default to INFO

        self.logger.setLevel(log_level)

        # Only add handler if not already added to avoid duplicate messages
        if not self.logger.handlers:
            ch = logging.StreamHandler()  # Create console handler
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def weather_station_mapping(self):
        """Load the weather station data from the web into ``self.weather_df``."""
        self.weather_df = read_from_web_CSV(self.weather_station_data)
        self.logger.info("Successfully loaded weather station data from the web.")
        # Here, you can apply any initial transformations to self.weather_df if necessary.

    def extract_measurement(self, message):
        """Extract the measurement type and value from a single message."""
        for key, pattern in self.patterns.items():
            match = re.search(pattern, message)
            if match:
                self.logger.debug(f"Measurement extracted: {key}")
                return key, float(next((x for x in match.groups() if x is not None)))
        self.logger.debug("No measurement match found.")
        return None, None

    def process_messages(self):
        """Apply :meth:`extract_measurement` to every message in the data."""
        if self.weather_df is not None:
            result = self.weather_df['Message'].apply(self.extract_measurement)
            self.weather_df['Measurement'], self.weather_df['Value'] = zip(*result)
            self.logger.info("Messages processed and measurements extracted.")
        else:
            self.logger.warning("weather_df is not initialized, skipping message processing.")
        return self.weather_df

    def calculate_means(self):
        """Return the mean of each measurement per weather station."""
        if self.weather_df is not None:
            means = self.weather_df.groupby(by=['Weather_station_ID', 'Measurement'])['Value'].mean()
            self.logger.info("Mean values calculated.")
            return means.unstack()
        else:
            self.logger.warning("weather_df is not initialized, cannot calculate means.")
            return None

    def process(self):
        """Run the full weather-data pipeline in order."""
        self.weather_station_mapping()  # Load and assign data to weather_df
        self.process_messages()  # Process messages to extract measurements
        self.logger.info("Data processing completed.")
