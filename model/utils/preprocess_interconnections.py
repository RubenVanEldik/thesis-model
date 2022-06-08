from datetime import datetime
import os
import pandas as pd

import utils
import validate


def preprocess_interconnections(interconnection_type, year):
    """
    Create separate CSV files for the HVAC, HVDC, and limits data
    """
    assert validate.is_interconnection_type(interconnection_type)
    assert validate.is_model_year(year)

    # Get the interconnections filepath
    input_directory = "./input/eraa/Transfer Capacities"
    output_directory = f"./input/interconnections/{year}"
    filepath = f"./{input_directory}/Transfer Capacities_ERAA2021_TY{year}.xlsx"

    # Create the output directory if does not exist yet
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    if interconnection_type == "hvac":
        hvac = pd.read_excel(filepath, sheet_name="HVAC", index_col=[0, 1], skiprows=10, header=[0, 1])
        hvac = hvac[sorted(hvac.columns)]
        hvac.index = utils.create_datetime_index(hvac.index, year)
        hvac.to_csv(f"{output_directory}/hvac.csv")

    if interconnection_type == "hvdc":
        hvdc = pd.read_excel(filepath, sheet_name="HVDC", index_col=[0, 1], skiprows=10, header=[0, 1])
        hvdc = hvdc[sorted(hvdc.columns)]
        hvdc.index = utils.create_datetime_index(hvdc.index, year)
        hvdc.to_csv(f"{output_directory}/hvdc.csv")

    if interconnection_type == "limits":
        limits = pd.read_excel(filepath, sheet_name="Max limit", index_col=[0, 1], skiprows=9)
        limits = limits.drop(index=("Country Level Maximum NTC ", "UTC"))
        limits = limits[sorted(limits.columns)]
        limits.index = utils.create_datetime_index(limits.index, year)
        limits.to_csv(f"{output_directory}/limits.csv")
