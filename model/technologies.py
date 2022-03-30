import pandas as pd
import streamlit as st
import utils


def assumptions(type, technology=None):
    """
    Return the assumptions dictionary for a specific technology
    """
    assumptions = utils.open_yaml("../input/technologies/assumptions.yaml")

    if technology is None:
        return assumptions[type]
    return assumptions[type][technology]


@st.experimental_memo
def import_technologies():
    """
    Import the technology data from NREL's Annual Technology Baseline
    """
    return pd.read_csv("../input/technologies/annual_technology_baseline.csv", index_col=0)


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


def get_pv_param(technology, *, year, parameter):
    """
    Return the value of a specific solar PV parameter
    """
    # Import the technology data
    df = import_technologies()

    # Filter the DataFrame
    df = df[df.technology == technology]
    df = df[df.core_metric_variable == year]
    df = df[df.core_metric_parameter == parameter]
    df = df[df.core_metric_case == "Market"]
    df = df[df.crpyears == 30]
    df = df[df.scenario == "Moderate"]

    # Don't filter on class for the WACC
    if parameter not in ["WACC Nominal", "WACC Real"]:
        df = df[df.techdetail == "Class4"]  # Class does not affect the costs for PV

    # Some values have a double value, use the key that starts with an 'R'
    if df.shape[0] == 2:
        df = df[df.core_metric_key.str.startswith("R")]

    # Throw an error if the final DataFrame does not have 1 row
    if df.shape[0] != 1:
        raise ValueError("Ended with more than 1 value")

    # Return the value of the last row
    return df.iloc[0].value


def get_wind_param(technology, *, year, parameter, resource_class):
    """
    Return the value of a specific wind parameter
    """
    # Import the technology data
    df = import_technologies()

    # Filter the technology DataFrame
    df = df[df.technology == technology]
    df = df[df.core_metric_variable == year]
    df = df[df.core_metric_parameter == parameter]
    df = df[df.core_metric_case == "Market"]
    df = df[df.crpyears == 30]
    df = df[df.scenario == "Moderate"]

    # Don't filter on class for the WACC
    if parameter not in ["WACC Nominal", "WACC Real"]:
        df = df[df.techdetail == resource_class]

    # Some values have a double value, use the key that starts with an 'R'
    if df.shape[0] == 2:
        df = df[df.core_metric_key.str.startswith("R")]

    # Throw an error if the final DataFrame does not have 1 row
    if df.shape[0] != 1:
        raise ValueError("Ended with more than 1 value")

    # Return the value of the last row
    return df.iloc[0].value
