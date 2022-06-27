import streamlit as st

import validate


@st.experimental_memo(show_spinner=False)
def format_str(str):
    """
    Replace underscores with spaces, capitalize the string, and convert the abbreviations into uppercase
    """
    assert validate.is_string(str)

    new_str = str.replace("_", " ").capitalize()

    # Format the abbreviations in uppercase
    abbreviations = ["lcoe", "hvac", "hvdc"]
    for abbreviation in abbreviations:
        new_str = new_str.replace(abbreviation, abbreviation.upper())
        new_str = new_str.replace(abbreviation.capitalize(), abbreviation.upper())

    return new_str
