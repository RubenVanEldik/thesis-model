import gurobipy as gp
import geopandas as gpd
import pandas as pd
import pyproj
from sklearn.linear_model import LinearRegression
import streamlit as st
import re
import yaml

import technologies
import validate


@st.experimental_memo(show_spinner=False)
def read_csv(filepath, **kwargs):
    """
    Read, cache, and return a CSV file
    """
    return pd.read_csv(filepath, **kwargs)


def read_hourly_data(filepath, *, start=None, end=None):
    """
    Returns the hourly data, if specified only for a specific date range
    """
    assert validate.is_filepath(filepath, suffix=".csv")
    assert validate.is_date(start, required=False)
    assert validate.is_date(end, required=False)

    hourly_data = read_csv(filepath, parse_dates=True, index_col=0)

    # Set the time to the beginning and end of the start and end date respectively
    start = start.strftime("%Y-%m-%d 00:00:00") if start else None
    end = end.strftime("%Y-%m-%d 23:59:59") if end else None

    # Return the hourly data
    return hourly_data[start:end]


@st.experimental_memo
def read_yaml(filepath):
    """
    Returns the content of a .yaml file as python list or dictionary
    """
    assert validate.is_filepath(filepath, suffix=".yaml")

    # Read and parse the file
    with open(filepath) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)


def write_yaml(filepath, data):
    """
    Store a dictionary or list as .yaml file
    """
    assert validate.is_filepath(filepath, suffix=".yaml")
    assert validate.is_dict_or_list(data)

    # Read and parse the file
    with open(filepath, "w") as f:
        return yaml.dump(data, f, Dumper=yaml.Dumper)


def store_text(filepath, text):
    """
    Store a string as .txt file
    """
    assert validate.is_filepath(filepath, suffix=".txt")
    assert validate.is_string(text, min_length=1)

    with open(filepath, "w") as f:
        f.write(text)


@st.experimental_memo
def read_shapefile(filepath):
    """
    Returns the content of a .shp file as a geopandas DataFrame
    """
    assert validate.is_filepath(filepath, suffix=".shp")

    # Read and return the file
    return gpd.read_file("../input/countries/ne_10m_admin_0_map_subunits.shp")


def get_geometries_of_countries(country_codes):
    """
    Return a geopandas DataFrame with the geometries for the specified countries
    """
    assert validate.is_list_like(country_codes)

    # Get a list of all included geographic units and all excluded geographic sub-units
    included_geographic_units = []
    excluded_geographic_subunits = []
    countries = read_yaml("../input/countries.yaml")
    relevant_countries = [country for country in countries if country["nuts_2"] in country_codes]
    for country in relevant_countries:
        included_geographic_units.extend(country.get("included_geographic_units") or [])
        excluded_geographic_subunits.extend(country.get("excluded_geographic_subunits") or [])

    # Get a Geopandas DataFrame with the relevant rows
    map_df = read_shapefile("../input/countries/ne_10m_admin_0_map_subunits.shp")
    map_df = map_df[map_df.GU_A3.isin(included_geographic_units)]
    map_df = map_df[~map_df.SU_A3.isin(excluded_geographic_subunits)]

    # Merge the regions for each country and set the nuts_2 country code as the index
    map_df = map_df.dissolve(by="SOV_A3")
    map_df["nuts_2"] = map_df.apply(lambda row: next(country["nuts_2"] for country in relevant_countries if country["alpha_3"] == row.ADM0_A3), axis=1)
    map_df = map_df.set_index("nuts_2")

    # Return a DataFrame with only the 'geometry' column
    return map_df[["geometry"]]


@st.experimental_memo
def calculate_distance(point1, point2):
    """
    Return the distance in meters between two points
    """
    assert validate.is_point(point1)
    assert validate.is_point(point2)

    geod = pyproj.Geod(ellps="WGS84")
    angle1, angle2, distance = geod.inv(point1.x, point1.y, point2.x, point2.y)

    return distance


@st.experimental_memo
def calculate_r_squared(col1, col2):
    """
    Calculate the R-squared value for two Series
    """
    assert validate.is_series(col1)
    assert validate.is_series(col2)

    # Initialize the linear regression model
    model = LinearRegression()

    # Set the X and y values
    X = col1.to_frame()
    y = col2

    # Fit the regression model and calculate the R-squared value
    model.fit(X, y)
    r_squared = model.score(X, y)

    # Return the R-squared value
    return r_squared


def calculate_linear_regression_line(col1, col2):
    """
    Calculate the X and Y values for a linear regression line
    """
    assert validate.is_series(col1)
    assert validate.is_series(col2)

    # Initialize the linear regression model
    model = LinearRegression()

    # Set the X and y values
    X = col1.to_frame()
    y = col2

    # Fit the regression model and calculate the R-squared value
    model.fit(X, y)

    # Return the R-squared value
    return X, model.predict(X)


def get_nested_key(dict, key_string):
    """
    Return the value of a nested key, specified as a dot separated string
    """

    # Start off pointing at the original dictionary that was passed in
    here = dict
    keys = key_string.split(".")

    # For each key in key_string set here to its value
    for key in keys:
        if here.get(key) is None:
            raise ValueError(f"Can not find '{key}' in '{key_string}'")
        here = here[key]

    # Return the final nested value
    return here


def set_nested_key(dict, key_string, value):
    """
    Set the value of a nested key, specified as a dot separated string
    """

    # Start off pointing at the original dictionary that was passed in
    here = dict
    keys = key_string.split(".")

    # For each key in key_string set here to its value
    for key in keys[:-1]:
        if here.get(key) is None:
            raise ValueError(f"Can not find '{key}' in '{key_string}'")
        here = here[key]

    # Set the final key to the given value
    here[keys[-1]] = value


def find_common_columns(dfs):
    """
    Return a list of the columns that appear in all DataFrames
    """
    assert validate.is_dataframe_dict(dfs)

    common_columns = None
    for df in dfs.values():
        if common_columns is None:
            common_columns = df.columns
        else:
            common_columns = common_columns & df.columns

    return list(common_columns)


@st.experimental_memo
def format_str(str):
    """
    Replace underscores with spaces and capitalize the string
    """
    assert validate.is_string(str)

    return str.replace("_", " ").capitalize()


@st.experimental_memo
def format_column_name(str):
    """
    Properly format any column name
    """
    assert validate.is_string(str)

    match = re.search("(.+)_(\w+)$", str)
    label = match.group(1)
    unit = match.group(2)

    # Replace all underscores with spaces and use the proper technology labels before capitalizing the first letter
    label = " ".join([(technologies.labelize(label_part, capitalize=False) if validate.is_technology(label_part) else label_part) for label_part in label.split("_")])
    label = label[0].upper() + label[1:]

    return f"{label} ({unit})"


@st.experimental_memo
def get_country_of_bidding_zone(bidding_zone):
    """
    Find to which country a bidding zone belongs to
    """
    assert validate.is_bidding_zone(bidding_zone)

    countries = read_yaml(f"../input/countries.yaml")
    return next(country["nuts_2"] for country in countries if bidding_zone in country["zones"])


def get_interconnections(bidding_zone, *, config, type, direction="export"):
    """
    Find the relevant interconnections for a bidding zone
    """
    assert validate.is_bidding_zone(bidding_zone)
    assert validate.is_config(config)
    assert validate.is_interconnection_type(type)
    assert validate.is_interconnection_direction(direction)

    filepath = f"../input/interconnections/{config['model_year']}/{type}.csv"
    interconnections = read_csv(filepath, parse_dates=True, index_col=0, header=[0, 1])

    relevant_interconnections = []
    for country in config["countries"]:
        for zone in country["zones"]:
            interconnection = (bidding_zone, zone) if direction == "export" else (zone, bidding_zone)
            if interconnection in interconnections:
                relevant_interconnections.append(interconnection)
    return interconnections[relevant_interconnections]


def merge_dataframes_on_column(dfs, column, *, sorted=False):
    """
    Create one DataFrame from a dictionary of DataFrames by selecting only one column per DataFrame
    """
    assert validate.is_dataframe_dict(dfs)
    assert validate.is_string(column)
    assert validate.is_bool(sorted)

    # Initialize a new DataFrame
    df = pd.DataFrame()

    # Add each (sorted) column to the new DataFrame
    for key in dfs:
        if sorted:
            col = dfs[key].sort_values(column, ascending=False)[column]
            df[key] = col.tolist()
        else:
            df[key] = dfs[key][column]

    return df


def convert_variables_recursively(data):
    """
    Store a dictionary or list as .yaml file
    """
    if type(data) is dict:
        for key, value in data.items():
            data[key] = convert_variables_recursively(value)
        return data
    elif type(data) is list:
        return [convert_variables_recursively(value) for value in data]
    elif type(data) is pd.core.frame.DataFrame:
        return data.applymap(convert_variables_recursively)
    elif type(data) is gp.Var:
        return data.X
    elif type(data) in [gp.LinExpr, gp.QuadExpr]:
        return data.getValue()
    return data
