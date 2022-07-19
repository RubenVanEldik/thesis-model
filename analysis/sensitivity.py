import pandas as pd
import streamlit as st

import stats
import utils
import validate


def sensitivity(output_directory, resolution):
    """
    Analyze the sensitivity
    """
    assert validate.is_directory_path(output_directory)

    st.title("⚖️ Sensitivity analysis")

    st.sidebar.header("Options")

    # Get the sensitivity config and regular config
    sensitivity_config = utils.read_yaml(output_directory / "sensitivity.yaml")
    config = utils.read_yaml(output_directory / next(iter(sensitivity_config["steps"])) / "config.yaml")

    # Select a output variable to run the sensitivity analysis on
    statistic_options = ["firm_lcoe", "unconstrained_lcoe", "premium", "relative_curtailment", "production_capacity", "storage_capacity"]
    statistic_name = st.sidebar.selectbox("Output variable", statistic_options, format_func=utils.format_str)

    if statistic_name:
        # Create a Series with the sensitivity steps as rows
        steps = pd.Series(data=sensitivity_config["steps"].keys(), index=sensitivity_config["steps"].values())

        # Calculate the output for each sensitivity step
        if statistic_name == "production_capacity":
            data = steps.apply(lambda step: pd.Series(stats.production_capacity(output_directory / step, resolution)))
        elif statistic_name == "storage_capacity":
            storage_capacity_type = st.sidebar.selectbox("Storage capacity type", ["energy", "power"], format_func=utils.format_str)
            data = steps.apply(lambda step: pd.Series(stats.storage_capacity(output_directory / step, resolution, type=storage_capacity_type)))
        else:
            data = steps.apply(lambda step: getattr(stats, statistic_name)(output_directory / step, resolution))

        # Show a line chart with the output
        if "output" in data:
            st.line_chart(data.output)
        else:
            st.line_chart(data)
