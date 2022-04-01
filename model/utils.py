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
