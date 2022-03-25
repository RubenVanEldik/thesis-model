import streamlit as st
import yaml


@st.experimental_memo
def open_yaml(filepath):
    """
    Returns the content of a .yaml file as python list or dictionary
    """
    if not filepath.endswith(".yaml"):
        raise ValueError("The file has to end with '.yaml'")

    # Read and parse the file
    with open(filepath) as f:
        return yaml.load(f, Loader=yaml.BaseLoader)
