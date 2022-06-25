import os
import streamlit as st

import analysis
import utils


def run():
    # Get the previous runs
    previous_runs = utils.get_previous_runs()
    previous_completed_runs = [previous_run for previous_run in previous_runs if utils.validate_run(previous_run)]

    # Show a warning and return the function if there are no completed runs
    if not previous_completed_runs:
        st.sidebar.warning("There are no previous runs to analyze")
        return

    # Select the run to analyze
    selected_run = st.sidebar.selectbox("Previous runs", previous_completed_runs)

    # Select the resolution to show the data of
    config = utils.read_yaml(f"./output/{selected_run}/config.yaml")
    sorted_resolution_stages = utils.get_sorted_resolution_stages(config)
    selected_resolution = st.sidebar.selectbox("Resolution", sorted_resolution_stages)

    # Select the type of analysis
    if os.path.isfile(f"./output/{selected_run}/sensitivity.yaml"):
        analysis_type = "sensitivity"
    else:
        analysis_type_options = ["statistics", "temporal_results", "countries", "correlation", "duration_curve"]
        analysis_type = st.sidebar.radio("Type of analysis", analysis_type_options, format_func=utils.format_str)

    # Run the analysis
    st.sidebar.header("Options")
    getattr(analysis, analysis_type)(selected_run, selected_resolution)


run()
