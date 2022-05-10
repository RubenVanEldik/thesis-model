import streamlit as st

import chart
import utils
import validate


def countries(run_name):
    """
    Analyze the storage
    """
    assert validate.is_string(run_name)

    st.title("🎌 Countries")

    production_capacity = utils.get_production_capacity(run_name, group="country")
    pv_capacity = production_capacity.pv

    map = chart.Map(pv_capacity / 1000, label="PV capacity (GW)")
    st.pyplot(map.fig)
