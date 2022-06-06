import os
import streamlit as st

import analyze
import utils

# Select the run to analyze
previous_runs = utils.get_previous_runs()
selected_run = st.sidebar.selectbox("Previous runs", previous_runs)

# Select the type of analysis
if os.path.isfile(f"./output/{selected_run}/sensitivity.yaml"):
    analysis = "sensitivity"
else:
    analysis_options = ["statistics", "hourly_results", "countries", "correlation", "duration_curve"]
    analysis = st.sidebar.radio("Type of analysis", analysis_options, format_func=utils.format_str)

# Run the analysis
getattr(analyze, analysis)(selected_run)
