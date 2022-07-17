import streamlit as st

import analysis
import utils


def run():
    # Get the previous runs
    previous_runs = utils.get_previous_runs()

    # Show a warning and return the function if there are no completed runs
    if not previous_runs:
        st.sidebar.warning("There are no previous runs to analyze")
        return

    # Select the run to analyze
    selected_run = st.sidebar.selectbox("Previous runs", previous_runs)
    output_directory = utils.path("output", selected_run)
    is_sensitivity_analysis = (output_directory / "sensitivity.yaml").is_file()

    # Get the config
    if is_sensitivity_analysis:
        # Get the config for the first step
        sensitivity_config = utils.read_yaml(output_directory / "sensitivity.yaml")
        first_step = next(iter(sensitivity_config["steps"]))
        config = utils.read_yaml(output_directory / first_step / "config.yaml")
    else:
        config = utils.read_yaml(output_directory / "config.yaml")

    # Select the resolution to show the data of
    sorted_resolution_stages = utils.get_sorted_resolution_stages(config)
    selected_resolution = st.sidebar.selectbox("Resolution", sorted_resolution_stages)

    # Select the type of analysis
    if is_sensitivity_analysis:
        analysis_type = "sensitivity"
    else:
        analysis_type_options = ["statistics", "temporal_results", "countries", "correlation", "duration_curve", "optimization_log"]
        analysis_type = st.sidebar.radio("Type of analysis", analysis_type_options, format_func=utils.format_str)

    # Run the analysis
    getattr(analysis, analysis_type)(output_directory, selected_resolution)


run()
