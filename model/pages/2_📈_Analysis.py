import os
import streamlit as st

import analysis
import utils

# Select the run to analyze
previous_runs = utils.get_previous_runs()
selected_run = st.sidebar.selectbox("Previous runs", previous_runs)

# Select the type of analysis
if os.path.isfile(f"./output/{selected_run}/sensitivity.yaml"):
    analysis_type = "sensitivity"
else:
    analysis_type_options = ["statistics", "hourly_results", "countries", "correlation", "duration_curve"]
    analysis_type = st.sidebar.radio("Type of analysis", analysis_type_options, format_func=utils.format_str)

# Run the analysis
st.sidebar.header("Options")
getattr(analysis, analysis_type)(selected_run)
