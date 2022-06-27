import geopandas as gpd
import streamlit as st

import validate


@st.experimental_memo(show_spinner=False)
def read_shapefile(filepath):
    """
    Returns the content of a .shp file as a geopandas DataFrame
    """
    assert validate.is_filepath(filepath, suffix=".shp")

    # Read and return the file
    return gpd.read_file(filepath)
