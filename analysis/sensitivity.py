import pandas as pd
import streamlit as st

import chart
import colors
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

    # Create a Series with the sensitivity steps as rows
    if sensitivity_config["analysis_type"] == "curtailment":
        # Use the actual curtailment as the index
        step_index = [stats.relative_curtailment(output_directory / step, resolution) for step in sensitivity_config["steps"].keys()]
    else:
        step_index = sensitivity_config["steps"].values()
    steps = pd.Series(data=sensitivity_config["steps"].keys(), index=step_index).sort_index()

    # Create the figure for the sensitivity plot
    sensitivity_plot = chart.Chart(xlabel=None, ylabel=None)

    # Ask for the breakdown level and if the cumulative results should be shown
    if statistic_name in ["firm_lcoe", "unconstrained_lcoe", "premium"]:
        breakdown_level_options = {0: "Off", 1: "Production and storage", 2: "Technologies"}
        breakdown_level = st.sidebar.selectbox("Breakdown level", breakdown_level_options, format_func=lambda key: breakdown_level_options[key])
        if breakdown_level in [1, 2]:
            show_cumulative_results = st.sidebar.checkbox("Show cumulative results")

    # Add the output for the sensitivity steps to the sensitivity plot
    if statistic_name in ["firm_lcoe", "unconstrained_lcoe", "premium"]:
        # Get the data and set the label
        if statistic_name == "firm_lcoe":
            sensitivity_plot.ax.set_ylabel("Firm LCOE (€/MWh)")
            data = steps.apply(lambda step: stats.firm_lcoe(output_directory / step, resolution, breakdown_level=breakdown_level))
        if statistic_name == "unconstrained_lcoe":
            sensitivity_plot.ax.set_ylabel("Unconstrained LCOE (€/MWh)")
            data = steps.apply(lambda step: stats.unconstrained_lcoe(output_directory / step, resolution, breakdown_level=breakdown_level))
        if statistic_name == "premium":
            sensitivity_plot.ax.set_ylabel("Premium (%)")
            data = steps.apply(lambda step: stats.premium(output_directory / step, resolution, breakdown_level=breakdown_level))

        # Plot the data depending on the breakdown level
        if breakdown_level == 0:
            sensitivity_plot.ax.plot(data, color=colors.primary())
        elif breakdown_level == 1:
            if show_cumulative_results:
                sensitivity_plot.ax.plot(data.sum(axis=1), color=colors.tertiary(), label="Total")
            sensitivity_plot.ax.plot(data["production"], color=colors.technology_type("production"), label="Production")
            sensitivity_plot.ax.plot(data["storage"], color=colors.technology_type("storage"), label="Storage")
            sensitivity_plot.ax.legend()
        else:
            if show_cumulative_results:
                sensitivity_plot.ax.plot(data.sum(axis=1), color=colors.tertiary(), label="Total")
            for technology in data:
                sensitivity_plot.ax.plot(data[technology], color=colors.technology(technology), label=utils.format_technology(technology))
            sensitivity_plot.ax.legend()
    if statistic_name == "relative_curtailment":
        data = steps.apply(lambda step: stats.relative_curtailment(output_directory / step, resolution))
        sensitivity_plot.ax.set_ylabel("Relative curtailment (%)")
        sensitivity_plot.ax.plot(data, color=colors.primary())
        sensitivity_plot.format_yticklabels("{:,.0%}")
    if statistic_name == "production_capacity":
        data = steps.apply(lambda step: pd.Series(stats.production_capacity(output_directory / step, resolution))) / 1000
        for production_technology in data:
            sensitivity_plot.ax.plot(data[production_technology], color=colors.technology(production_technology), label=utils.format_technology(production_technology))
        sensitivity_plot.ax.set_ylabel("Production capacity (GW)")
        sensitivity_plot.ax.legend()
    if statistic_name == "storage_capacity":
        storage_capacity_type = st.sidebar.selectbox("Storage capacity type", ["energy", "power"], format_func=utils.format_str)
        data = steps.apply(lambda step: pd.Series(stats.storage_capacity(output_directory / step, resolution, storage_type=storage_capacity_type)))
        data = data / 10 ** 6 if storage_capacity_type == "energy" else data / 10 ** 3
        for storage_technology in data:
            sensitivity_plot.ax.plot(data[storage_technology], color=colors.technology(storage_technology), label=utils.format_technology(storage_technology))
        unit = "TWh" if storage_capacity_type == "energy" else "GW"
        sensitivity_plot.ax.set_ylabel(f"Storage capacity ({unit})")
        sensitivity_plot.ax.legend()

    # Set the range of the y-axis
    col1, col2 = st.sidebar.columns(2)
    default_y_limits = sensitivity_plot.ax.get_ylim()
    y_min = col1.number_input("Min y-axis", value=default_y_limits[0])
    y_max = col2.number_input("Max y-axis", value=default_y_limits[1])
    sensitivity_plot.set_y_limits(y_min=y_min, y_max=y_max)

    # Format the axes
    if sensitivity_config["analysis_type"] == "curtailment":
        sensitivity_plot.ax.set_xlabel("Curtailment (%)")
        sensitivity_plot.format_xticklabels("{:,.0%}")
        sensitivity_plot.set_x_limits(x_min=0, x_max=1)
    elif sensitivity_config["analysis_type"] == "climate_years":
        sensitivity_plot.ax.set_xlabel("Number of climate years")
    elif sensitivity_config["analysis_type"] == "technology_scenario":
        sensitivity_plot.ax.set_xlabel("Technology scenario")
    elif sensitivity_config["analysis_type"] == "interconnection_capacity":
        sensitivity_plot.ax.set_xlabel("Relative interconnection capacity (%)")
        sensitivity_plot.format_xticklabels("{:,.0%}")
    elif sensitivity_config["analysis_type"] == "self_sufficiency":
        sensitivity_plot.ax.set_xlabel("Minimum self sufficiency (%)")
        sensitivity_plot.format_xticklabels("{:,.0%}")

    # Plot the sensitivity plot
    st.pyplot(sensitivity_plot.fig)
