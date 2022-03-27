import pandas as pd
import streamlit as st

technology_map = {
    "CommPV": {
        "crpyears": 30,
        "core_metric_case": "Market",
        "scenario": "Moderate",
        "techdetail": "Class4",
    }
}


@st.experimental_memo
def import_technologies():
    """
    Import the technology data from NREL's Annual Technology Baseline
    """
    return pd.read_csv("../input/technologies/atb.csv", index_col=0)


def get_technologies():
    """
    Return a list of all technologies in the ATB
    """
    df = import_technologies()
    return df.technology.unique()


def get_parameters(technology):
    """
    Return a list of all parameters for a specific technology
    """
    df = import_technologies()
    df = df[df.technology == technology]
    return df.core_metric_parameter.unique()


def get_value(technology, *, year, parameter):
    """
    Return the value of a specific parameter for a technology
    """
    # Validate the year
    if year < 2020 or year > 2050:
        raise ValueError("Invalid year")

    # Check if the technology could be found
    filters = technology_map.get(technology)
    if not filters:
        raise ValueError("Invalid technology")

    # Import the technology data
    df = import_technologies()

    # Filter the technology DataFrame
    df = df[df.technology == technology]
    df = df[df.core_metric_variable == year]
    df = df[df.core_metric_parameter == parameter]
    for filter_key in filters:
        df = df[df[filter_key] == filters[filter_key]]

    # Throw an error if the final DataFrame does not have 1 row
    if df.shape[0] != 1:
        raise ValueError("Ended with more than 1 value")

    # Return the value of the last row
    return df.iloc[0].value
