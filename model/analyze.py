import pandas as pd
import streamlit as st
import re

import chart
import colors
import lcoe
import technologies
import validate
import utils


@st.experimental_memo
def _get_production_capacity(run_name, *, group=None):
    """
    Return the (grouped) production capacity
    """
    assert validate.is_string(run_name)
    assert validate.is_aggregation_level(group, required=False)

    # Get the production data
    production_capacity = utils.read_csv(f"../output/{run_name}/capacities/production.csv", index_col=0)

    # Return all bidding zones individually if not grouped
    if group is None:
        return production_capacity

    # Return the sum of all bidding zones per country
    if group == "country":
        production_capacity["country"] = production_capacity.index.to_series().apply(utils.get_country_of_bidding_zone)
        grouped_production_capacity = production_capacity.groupby(["country"]).sum()
        return grouped_production_capacity

    # Return the sum of all bidding zones
    if group == "all":
        return production_capacity.sum()


@st.experimental_memo
def _get_storage_capacity(run_name, *, group=None):
    """
    Return the (grouped) storage capacity
    """
    assert validate.is_string(run_name)
    assert validate.is_aggregation_level(group, required=False)

    # Get the storage data
    storage_capacity = utils.read_csv(f"../output/{run_name}/capacities/storage.csv", index_col=0, header=[0, 1])

    # Return all bidding zones individually if not grouped
    if group is None:
        return storage_capacity

    # Return the sum of all bidding zones per country
    if group == "country":
        storage_capacity["country"] = storage_capacity.index.to_series().apply(utils.get_country_of_bidding_zone)
        grouped_storage_capacity = storage_capacity.groupby(["country"]).sum()
        return grouped_storage_capacity

    # Return the sum of all bidding zones
    if group == "all":
        return storage_capacity.sum()


@st.experimental_memo
def _get_hourly_results(run_name, *, group=None):
    """
    Return the (grouped) production capacity
    """
    assert validate.is_string(run_name)
    assert validate.is_aggregation_level(group, required=False)

    # Get the config
    config = utils.read_yaml(f"../output/{run_name}/config.yaml")

    # Get the hourly data for each bidding zone
    hourly_results = {}
    for country in config["countries"]:
        for bidding_zone in country["zones"]:
            filepath = f"../output/{run_name}/hourly_results/{bidding_zone}.csv"
            hourly_results[bidding_zone] = utils.read_hourly_data(filepath)

            if hourly_results[bidding_zone].isnull().values.any():
                st.warning(f"Bidding zone {bidding_zone} contains NaN values")

    # Return all bidding zones individually if not grouped
    if group is None:
        return hourly_results

    # Return the sum of all bidding zones per country
    if group == "country":
        hourly_results_per_country = {}
        for bidding_zone, hourly_results_local in hourly_results.items():
            country_code = utils.get_country_of_bidding_zone(bidding_zone)
            if hourly_results_per_country.get(country_code) is None:
                hourly_results_per_country[country_code] = hourly_results_local
            else:
                hourly_results_per_country[country_code] += hourly_results_local
        return hourly_results_per_country

    # Return the sum of all bidding zones
    if group == "all":
        total_hourly_results = None
        for hourly_results_local in hourly_results.values():
            if total_hourly_results is None:
                total_hourly_results = hourly_results_local.copy(deep=True)
            else:
                total_hourly_results += hourly_results_local
        return total_hourly_results


def hourly_results(run_name):
    """
    Show the hourly results in a chart and table
    """
    assert validate.is_string(run_name)

    st.title("🕰️ Hourly results")

    # Get hourly results for a country
    all_hourly_results = _get_hourly_results(run_name, group="country")
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


def statistics(run_name):
    """
    Show the key indicators for a run
    """
    assert validate.is_string(run_name)

    st.title("📊 Statistics")

    # Get both the grouped and ungrouped results
    hourly_results = _get_hourly_results(run_name)
    total_hourly_results = _get_hourly_results(run_name, group="all")
    production_capacity = _get_production_capacity(run_name)
    total_production_capacity = _get_production_capacity(run_name, group="all")
    storage_capacity = _get_storage_capacity(run_name)
    total_storage_capacity = _get_storage_capacity(run_name, group="all")

    # Show the KPI's
    st.header("KPI's")
    col1, col2, col3 = st.columns(3)
    config = utils.read_yaml(f"../output/{run_name}/config.yaml")
    firm_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results, technologies=config["technologies"])
    unconstrained_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results, technologies=config["technologies"], unconstrained=True)
    col1.metric("LCOE", f"{int(firm_lcoe)}€/MWh")
    firm_kwh_premium = firm_lcoe / unconstrained_lcoe
    col2.metric("Firm kWh premium", f"{firm_kwh_premium:.2f}")
    relative_curtailment = total_hourly_results.curtailed_MWh.sum() / total_hourly_results.production_total_MWh.sum()
    col3.metric("Curtailment", f"{relative_curtailment:.1%}")

    # Show the capacities
    st.header("Capacities")
    st.subheader("Production")
    cols = st.columns(max(len(total_production_capacity), 3))
    for index, technology in enumerate(total_production_capacity.index):
        cols[index].metric(technologies.labelize(technology), f"{int(total_production_capacity[technology] / 1000):,}GW")
    st.subheader("Storage")
    cols = st.columns(max(len(total_storage_capacity), 3))
    total_storage_capacity_energy = total_storage_capacity[total_storage_capacity.index.isin(["energy"], level=1)]
    for index, technology in enumerate(total_storage_capacity_energy.index):
        installed_hours = total_storage_capacity_energy[technology] / total_hourly_results.demand_MWh.mean()
        cols[index].metric(technologies.labelize(technology[0]), f"{installed_hours:.1f}Hr")


def countries(run_name):
    """
    Analyze the storage
    """
    assert validate.is_string(run_name)

    st.title("🎌 Countries")

    production_capacity = _get_production_capacity(run_name, group="country")
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
    all_hourly_results = _get_hourly_results(run_name, group="country")
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
    all_hourly_results = _get_hourly_results(run_name, group="country")

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
            production_capacity = _get_production_capacity(f"{run_name}/{step_key}")
            storage_capacity = _get_storage_capacity(f"{run_name}/{step_key}")
            hourly_results = _get_hourly_results(f"{run_name}/{step_key}")
            config = utils.read_yaml(f"../output/{run_name}/{step_key}/config.yaml")

            firm_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results, technologies=config["technologies"])
            output_values.loc[step_value, "LCOE"] = firm_lcoe

        # Show a line chart with the selected output variables
        st.line_chart(output_values[output_variables])
