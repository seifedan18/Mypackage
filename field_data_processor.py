"""Field data processing for the Maji Ndogo data pipeline.

This module defines :class:`FieldDataProcessor`, a class that encapsulates the
whole process of ingesting and cleaning the field related data:

1. ingest the data from the SQL database,
2. swap the mislabelled ``Annual_yield`` and ``Crop_type`` columns,
3. correct the elevation values and the crop type spelling mistakes, and
4. map each field to its nearest weather station.

The configuration (database path, SQL query, columns/values to rename and the
weather mapping CSV URL) is supplied through a ``config_params`` dictionary so
that all pipeline settings live in one central place.
"""

import pandas as pd
from data_ingestion import create_db_engine, query_data, read_from_web_CSV
import logging


class FieldDataProcessor:
    """Ingest and clean the field related data into a single DataFrame."""

    def __init__(self, config_params, logging_level="INFO"):
        """Initialise the processor from a configuration dictionary.

        Parameters
        ----------
        config_params : dict
            Dictionary with the keys ``'db_path'``, ``'sql_query'``,
            ``'columns_to_rename'``, ``'values_to_rename'`` and
            ``'weather_mapping_csv'``.
        logging_level : str, optional
            One of ``"DEBUG"``, ``"INFO"`` or ``"NONE"``. Defaults to
            ``"INFO"``.
        """
        self.db_path = config_params['db_path']
        self.sql_query = config_params['sql_query']
        self.columns_to_rename = config_params['columns_to_rename']
        self.values_to_rename = config_params['values_to_rename']
        self.weather_map_data = config_params['weather_mapping_csv']

        self.initialize_logging(logging_level)

        # We create empty objects to store the DataFrame and engine in
        self.df = None
        self.engine = None

    def initialize_logging(self, logging_level):
        """Set up logging for this instance of FieldDataProcessor."""
        logger_name = __name__ + ".FieldDataProcessor"
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

    def ingest_sql_data(self):
        """Create the engine, run the query and store the resulting DataFrame."""
        self.engine = create_db_engine(self.db_path)
        self.df = query_data(self.engine, self.sql_query)
        self.logger.info("Sucessfully loaded data.")
        return self.df

    def rename_columns(self):
        """Swap the names of the two mislabelled columns in ``self.df``."""
        # Extract the columns to rename from the configuration
        column1, column2 = list(self.columns_to_rename.keys())[0], list(self.columns_to_rename.values())[0]

        # Temporarily rename one of the columns to avoid a naming conflict
        temp_name = "__temp_name_for_swap__"
        while temp_name in self.df.columns:
            temp_name += "_"

        # Perform the swap
        self.df = self.df.rename(columns={column1: temp_name, column2: column1})
        self.df = self.df.rename(columns={temp_name: column2})

        self.logger.info(f"Swapped columns: {column1} with {column2}")

    def apply_corrections(self, column_name='Crop_type', abs_column='Elevation'):
        """Fix negative elevations and correct the crop type values."""
        self.df[abs_column] = self.df[abs_column].abs()
        self.df[column_name] = self.df[column_name].str.strip()
        self.df[column_name] = self.df[column_name].apply(lambda crop: self.values_to_rename.get(crop, crop))

    def weather_station_mapping(self):
        """Merge the weather-station-to-field mapping into ``self.df``."""
        self.df = self.df.merge(read_from_web_CSV(self.weather_map_data), on='Field_ID', how='left')
        self.df = self.df.drop(columns="Unnamed: 0")
        return self.df

    def process(self):
        """Run the full field-data pipeline in order."""
        self.ingest_sql_data()
        self.rename_columns()
        self.apply_corrections()
        self.weather_station_mapping()
