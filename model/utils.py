import gurobipy as gp
import pandas as pd
import streamlit as st
import yaml

import validate


@st.experimental_memo
def open_yaml(filepath):
    """
    Returns the content of a .yaml file as python list or dictionary
    """
    assert validate.is_filepath(filepath, suffix=".yaml")

    # Read and parse the file
    with open(filepath) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)


@st.experimental_memo
def store_yaml(filepath, data):
    """
    Store a dictionary or list as .yaml file
    """
    assert validate.is_filepath(filepath, suffix=".yaml")
    assert validate.is_dict_or_list(data)

    # Read and parse the file
    with open(filepath, "w") as f:
        return yaml.dump(data, f, Dumper=yaml.Dumper)


def convert_variables_recursively(data):
    if type(data) is dict:
        for key, value in data.items():
            data[key] = convert_variables_recursively(value)
    elif type(data) is list:
        for index, value in enumerate(data):
            data[index] = convert_variables_recursively(value)
    elif type(data) is pd.core.frame.DataFrame:
        data = data.applymap(convert_variables_recursively)
    elif type(data) is gp.Var:
        data = data.X
    elif type(data) in [gp.LinExpr, gp.QuadExpr]:
        data = data.getValue()
    return data
