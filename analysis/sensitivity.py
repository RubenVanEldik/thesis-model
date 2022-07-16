import pandas as pd
import streamlit as st

import stats
import utils
import validate


def sensitivity(run_name, resolution):
    """
    Analyze the sensitivity
    """
    assert validate.is_string(run_name)

    st.title("⚖️ Sensitivity analysis")

    st.sidebar.header("Options")

    # Get the sensitivity analysis
    sensitivity_config = utils.read_yaml(utils.path("output", run_name, "sensitivity.yaml"))

    # Select a output variable to run the sensitivity analysis on
    statistic_options = ["firm_lcoe", "unconstrained_lcoe", "premium", "relative_curtailment", "production_capacity", "storage_capacity"]
    statistic_name = st.sidebar.selectbox("Output variable", statistic_options, format_func=utils.format_str)

    if statistic_name:
        # Create a DataFrame with the sensitivity steps as rows
        data = pd.Series(data=sensitivity_config["steps"], name="input").to_frame()

        # Calculate the output for each sensitivity step
        output_directory = utils.path("output", run_name)
        data["output"] = data.apply(lambda row: getattr(stats, statistic_name)(output_directory / row.name, resolution), axis=1)

        # Show a line chart with the output
        st.line_chart(data.output)
