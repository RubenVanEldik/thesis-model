import pandas as pd
from datetime import datetime
import utils


def get_bidding_zones():
    """
    Returns all bidding zones using the demand Excel file for 2030
    """
    xl = pd.ExcelFile(f"../input/eraa/Demand Data/Demand_TimeSeries_2030_NationalEstimates.xlsx")
    return xl.sheet_names


def get_relevant_sheet_names(filename, zone):
    """
    Returns the relevant Excel sheets for a specific bidding zone
    """

    def sheet_belongs_to_zone(sheet, zone):
        """
        Check if a specific sheet belongs to a bidding zone
        """
        # Return True if its an exact match
        if sheet == zone:
            return True

        # If the country has only 1 bidding zone, just check the first two letters
        if len([z for z in bidding_zones if z.startswith(zone[:2])]) < 2:
            return sheet.startswith(zone[:2])

        exceptions = {
            "DKKF": None,
            "FR01": "FR00",
            "FR02": "FR00",
            "FR03": "FR00",
            "FR04": "FR00",
            "FR05": "FR00",
            "FR06": "FR00",
            "FR07": "FR00",
            "FR08": "FR00",
            "FR09": "FR00",
            "FR10": "FR00",
            "FR11": "FR00",
            "FR12": "FR00",
            "FR13": "FR00",
            "FR14": "FR00",
            "GR01": "GR00",
            "GR02": "GR00",
            "LU00": None,
            "LUV1": None,
            "NOS1": "NOS0",
            "NOS2": "NOS0",
            "NOS3": "NOS0",
            "UK01": "UK00",
            "UK02": "UK00",
            "UK03": "UK00",
            "UK04": "UK00",
            "UK05": "UK00",
        }

        # Check if the zone is part of the exception list
        if exceptions.get(sheet) is not None:
            return exceptions.get(sheet) == zone

        # Return false if its not an exact match, the country has multiple bidding zones and its not an exception
        return False

    # Return a sorted list of all relevant sheet names
    relevant_sheet_names = [
        sheet_name
        for sheet_name in pd.ExcelFile(filename).sheet_names
        if sheet_belongs_to_zone(sheet_name, zone)
    ]
    relevant_sheet_names.sort()
    return relevant_sheet_names


def import_data(data, filename, *, bidding_zone, column_name=None):
    """
    Find and add all the relevant columns from a specific Excel file to the data DataFrame
    """
    relevant_zones = get_relevant_sheet_names(filename, bidding_zone)
    for zone in relevant_zones:
        # Import the Excel sheet for a zone
        sheet = pd.read_excel(
            filename,
            sheet_name=zone,
            index_col=[0, 1],
            skiprows=10,
            usecols=lambda col: col in ["Date", "Hour"] or isinstance(col, int),
        )

        # Transform the sheet DataFrame to a Series with appropriate index
        new_column = pd.Series([], dtype="float64")
        for year_column in sheet.columns:
            data_year = sheet[year_column]
            data_year.index = utils.create_datetime_index(sheet.index, year_column)
            new_column = new_column.append(data_year)

        # Add the new column to the DataFrame or create a new data DataFrame if it doesn't exist yet
        formatted_column_name = column_name.replace("{zone}", zone[2:])
        if data is None:
            new_column.name = formatted_column_name
            data = new_column.to_frame()
        else:
            data[formatted_column_name] = new_column

    # Return the DataFrame with the newly created column
    return data


if __name__ == "__main__":
    bidding_zones = get_bidding_zones()

    # Loop over all bidding zones for both 2025 and 2030
    for year in [2025, 2030]:
        for zone in bidding_zones:
            print(f"Importing all data for {zone} for {year} ({datetime.now()})")
            # Import demand data
            data = import_data(
                None,
                f"../input/eraa/Demand Data/Demand_TimeSeries_{year}_NationalEstimates.xlsx",
                bidding_zone=zone,
                column_name="demand_MWh",
            )

            # Import PV data
            data = import_data(
                data,
                f"../input/eraa/Climate Data/PECD_LFSolarPV_{year}_edition 2021.3.xlsx",
                bidding_zone=zone,
                column_name="pv_{zone}_cf",
            )

            # Import onshore wind data
            data = import_data(
                data,
                f"../input/eraa/Climate Data/PECD_Onshore_{year}_edition 2021.3.xlsx",
                bidding_zone=zone,
                column_name="onshore_{zone}_cf",
            )

            # Import offshore wind data
            data = import_data(
                data,
                f"../input/eraa/Climate Data/PECD_Offshore_{year}_edition 2021.3.xlsx",
                bidding_zone=zone,
                column_name="offshore_{zone}_cf",
            )

            # Store the data in a CSV file
            data.to_csv(f"../input/bidding_zones/{year}/{zone}.csv")
