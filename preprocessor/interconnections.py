import pandas as pd
from datetime import datetime
import utils


if __name__ == "__main__":
    # Loop over all interconnection types for both 2025 and 2030
    for year in [2025, 2030]:
        print(f"Importing all interconnection data for {year} ({datetime.now()})")

        # Get the interconnections filepath
        folder = "../input/eraa/Transfer Capacities"
        filepath = f"{folder}/Transfer Capacities_ERAA2021_TY{year}.xlsx"

        # Preprocess HVAC data
        hvac = pd.read_excel(
            filepath, sheet_name="HVAC", index_col=[0, 1], skiprows=10, header=[0, 1]
        )
        hvac = hvac[sorted(hvac.columns)]
        hvac.index = utils.create_datetime_index(hvac.index, year)
        hvac.to_csv(f"../input/interconnections/{year}/hvac.csv")

        # Preprocess HVDC data
        hvdc = pd.read_excel(
            filepath, sheet_name="HVDC", index_col=[0, 1], skiprows=10, header=[0, 1]
        )
        hvdc = hvdc[sorted(hvdc.columns)]
        hvdc.index = utils.create_datetime_index(hvdc.index, year)
        hvdc.to_csv(f"../input/interconnections/{year}/hvdc.csv")

        # Preprocess limit data
        limits = pd.read_excel(filepath, sheet_name="Max limit", index_col=[0, 1], skiprows=9)
        limits = limits.drop(index=("Country Level Maximum NTC ", "UTC"))
        limits = limits[sorted(limits.columns)]
        limits.index = utils.create_datetime_index(limits.index, year)
        limits.to_csv(f"../input/interconnections/{year}/limits.csv")
