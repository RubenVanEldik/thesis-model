import streamlit as st

import validate


@st.experimental_memo(show_spinner=False)
def read_text(filepath):
    """
    Read a text file
    """
    assert validate.is_filepath(filepath, suffix=".txt")

    with open(filepath) as f:
        text = f.read()

    return text
