import pandas as pd
import streamlit as st

import validate


@st.experimental_memo(show_spinner=False)
def read_csv(filepath, **kwargs):
    """
    Read, cache, and return a CSV file
    """
    assert validate.is_filepath(filepath, suffix=".csv")

    return pd.read_csv(filepath, **kwargs)
