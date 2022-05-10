import streamlit as st

import validate


@st.experimental_memo(show_spinner=False)
def format_str(str):
    """
    Replace underscores with spaces and capitalize the string
    """
    assert validate.is_string(str)

    return str.replace("_", " ").capitalize()
