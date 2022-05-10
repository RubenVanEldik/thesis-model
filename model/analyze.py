import pandas as pd
import streamlit as st
import re

import chart
import colors
import lcoe
import technologies
import validate
import utils
import stats


def statistics(run_name):
    """
    Show the key indicators for a run
    """
    assert validate.is_string(run_name)

    st.title("📊 Statistics")

    # Ask for which countries the statistics should be shown
    config = utils.read_yaml(f"../output/{run_name}/config.yaml")
    selected_countries = st.multiselect("Countries", config["countries"], format_func=lambda country: country["name"])
    selected_country_codes = [country["nuts_2"] for country in selected_countries]

    # Show the KPI's
    with st.expander("KPI's", expanded=True):
        col1, col2, col3 = st.columns(3)

        # LCOE
        firm_lcoe_selected = stats.firm_lcoe(run_name, countries=selected_country_codes)
        firm_lcoe_all = stats.firm_lcoe(run_name)
        lcoe_delta = f"{(firm_lcoe_selected / firm_lcoe_all) - 1:.0%}" if selected_country_codes else None
        col1.metric("LCOE", f"{int(firm_lcoe_selected)}€/MWh", lcoe_delta, delta_color="inverse")

        # Firm kWh premium
        premium_selected = stats.premium(run_name, countries=selected_country_codes)
        premium_all = stats.premium(run_name)
        premium_delta = f"{(premium_selected / premium_all) - 1:.0%}" if selected_country_codes else None
        col2.metric("Firm kWh premium", f"{premium_selected:.2f}", premium_delta, delta_color="inverse")

        # Curtailment
        curtailment_selected = stats.relative_curtailment(run_name, countries=selected_country_codes)
        curtailment_all = stats.relative_curtailment(run_name)
        curtailment_delta = f"{(curtailment_selected / curtailment_all) - 1:.0%}" if selected_country_codes else None
        col3.metric("Curtailment", f"{curtailment_selected:.1%}", curtailment_delta, delta_color="inverse")

    # Show the capacities
    with st.expander("Production capacity"):
        production_capacity = stats.production_capacity(run_name, countries=selected_country_codes)
        cols = st.columns(max(len(production_capacity), 3))
        for index, technology in enumerate(production_capacity):
            cols[index].metric(technologies.labelize(technology), f"{int(production_capacity[technology] / 1000):,}GW")

    with st.expander("Storage capacity"):
        storage_capacity = stats.storage_capacity(run_name, type="energy", countries=selected_country_codes)
        cols = st.columns(max(len(storage_capacity), 3))
        for index, technology in enumerate(storage_capacity):
            technology_label = technologies.labelize(technology)
            cols[index].metric(f"{technology_label} energy", f"{storage_capacity[technology] / 10**6:.2f}TWh")


def hourly_results(run_name):
    """
    Show the hourly results in a chart and table
    """
    assert validate.is_string(run_name)

    st.title("🕰️ Hourly results")

    # Get hourly results for a country
    all_hourly_results = utils.get_hourly_results(run_name, group="country")
    config = utils.read_yaml(f"../output/{run_name}/config.yaml")
    country = st.selectbox("Country", config["countries"], format_func=lambda country: country["name"])
    hourly_results = all_hourly_results[country["nuts_2"]]

    # Filter the data columns
    hourly_results.columns = [utils.format_column_name(column_name) for column_name in hourly_results.columns]
    columns = st.multiselect("Columns", hourly_results.columns)
    hourly_results = hourly_results[columns]

    # Show the chart and DataFrame if any columns are selected
    if columns:
        # Filter the data temporarily
        start_data = hourly_results.index.min().to_pydatetime()
        end_data = hourly_results.index.max().to_pydatetime()
        data_range = st.slider("Date range", value=(start_data, end_data), min_value=start_data, max_value=end_data)
        hourly_results = hourly_results.loc[data_range[0] : data_range[1]]

        # Show the line chart
        st.line_chart(hourly_results)

        # Show the table in an expander
        with st.expander("Raw data"):
            st.dataframe(hourly_results)


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


def correlation(run_name):
    """
    Plot the correlation between the distance between of two countries and the value of a specific column
    """
    assert validate.is_string(run_name)

    st.title("📉 Correlation")

    # Get the hourly results and merge them on a single column
    all_hourly_results = utils.get_hourly_results(run_name, group="country")
    relevant_columns = utils.find_common_columns(all_hourly_results)
    column_name = st.selectbox("Column", relevant_columns, format_func=utils.format_column_name)
    hourly_results = utils.merge_dataframes_on_column(all_hourly_results, column_name)

    # Get the geometries and centroids for all countries
    geometries = utils.get_geometries_of_countries(all_hourly_results.keys())
    geometries["centroid"] = geometries.centroid

    # Calculate the distance and R-squared for each country pair
    index = [(column_name1, column_name2) for column_name1 in hourly_results for column_name2 in hourly_results if column_name1 < column_name2]
    columns = ["distance", "r_squared"]
    correlations = pd.DataFrame(index=index, columns=columns)
    correlations["distance"] = correlations.apply(lambda row: utils.calculate_distance(geometries.loc[row.name[0], "centroid"], geometries.loc[row.name[1], "centroid"]) / 1000, axis=1)
    correlations["r_squared"] = correlations.apply(lambda row: utils.calculate_r_squared(hourly_results[row.name[0]], hourly_results[row.name[1]]), axis=1)

    # Create a scatter plot
    correlation_plot = chart.Chart(xlabel="Distance (km)", ylabel="Coefficient of determination")
    correlation_plot.ax.scatter(correlations.distance, correlations.r_squared, color=colors.get("blue", 600), alpha=0.5)
    if st.checkbox("Show linear regression line"):
        trendline_x, trendline_y = utils.calculate_linear_regression_line(correlations.distance, correlations.r_squared)
        correlation_plot.ax.plot(trendline_x, trendline_y, color=colors.get("gray", 600))

    # Show the plot
    st.pyplot(correlation_plot.fig)


def duration_curve(run_name):
    """
    Analyze the storage
    """
    assert validate.is_string(run_name)

    st.title("⌛ Duration curve")

    # Get the storage capacity and hourly results
    all_hourly_results = utils.get_hourly_results(run_name, group="country")

    # Select a column as numerator and denominator
    st.subheader("Columns")
    first_country = next(iter(all_hourly_results))
    columns = all_hourly_results[first_country].columns
    relevant_columns = utils.find_common_columns(all_hourly_results)
    relative = st.checkbox("Relative")
    col1, col2 = st.columns(2)
    numerator = col1.selectbox("Numerator", relevant_columns, format_func=utils.format_column_name)
    denominator = col2.selectbox("Denominator", relevant_columns, format_func=utils.format_column_name) if relative else None

    # Set the label for the y-axis
    st.subheader("Axes")
    col1, col2 = st.columns(2)
    ylabel_match = re.search("(.+)_(\w+)$", numerator)
    ylabel_text = utils.format_str(ylabel_match.group(1))
    ylabel_unit = ylabel_match.group(2) if denominator is None else "%"
    xlabel = col1.text_input("Label x-axis", value="Time (%)")
    ylabel = col2.text_input("Label y-axis", value=f"{ylabel_text} ({ylabel_unit})")
    axis_scale_options = ["linear", "log", "symlog", "logit"]
    xscale = col1.selectbox("Scale x-axis", axis_scale_options, format_func=utils.format_str)
    yscale = col2.selectbox("Scale y-axis", axis_scale_options, format_func=utils.format_str)

    # Set the waterfall parameters
    st.subheader("Options")
    range_area = st.checkbox("Range area", value=True)
    individual_lines = st.checkbox("Individual lines", value=False)
    ignore_zeroes = st.checkbox("Ignore zeroes", value=False)
    unity_line = st.checkbox("Unity line", value=False)

    # Create two new DataFrames with only the numerator/denominator column and all values sorted
    waterfall_df = utils.merge_dataframes_on_column(all_hourly_results, numerator, sorted=True)
    if denominator:
        denominator_df = utils.merge_dataframes_on_column(all_hourly_results, denominator, sorted=True)
        waterfall_df = waterfall_df / denominator_df.max()

    # Create the plot
    plot = chart.waterfall(waterfall_df, is_relative=bool(denominator), xlabel=xlabel, ylabel=ylabel, xscale=xscale, yscale=yscale, individual_lines=individual_lines, range_area=range_area, ignore_zeroes=ignore_zeroes, unity_line=unity_line)
    st.pyplot(plot)


def sensitivity(run_name):
    """
    Analyze the sensitivity
    """
    assert validate.is_string(run_name)

    st.title("Sensitivity analysis")

    sensitivity_config = utils.read_yaml(f"../output/{run_name}/sensitivity.yaml")
    output_variable_options = ["LCOE"]
    output_variables = st.multiselect("Output variable", output_variable_options)
    if output_variables:
        sensitivity_steps = sensitivity_config["steps"]
        output_values = pd.DataFrame(index=sensitivity_steps.values(), columns=output_variable_options)

        # Loop over each step in the sensitivity analysis
        for step_key, step_value in sensitivity_steps.items():
            production_capacity = utils.get_production_capacity(f"{run_name}/{step_key}")
            storage_capacity = utils.get_storage_capacity(f"{run_name}/{step_key}")
            hourly_results = utils.get_hourly_results(f"{run_name}/{step_key}")
            config = utils.read_yaml(f"../output/{run_name}/{step_key}/config.yaml")

            hourly_demand = utils.merge_dataframes_on_column(hourly_results, "demand_MWh")
            firm_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_demand, technologies=config["technologies"])
            output_values.loc[step_value, "LCOE"] = firm_lcoe

        # Show a line chart with the selected output variables
        st.line_chart(output_values[output_variables])
