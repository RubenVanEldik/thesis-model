import pandas as pd
import re
import streamlit as st

import chart
import stats
import technologies
import utils
import validate


def _select_data(run_name, *, name):
    """
    Select the source of the data and the specific columns and aggregation type
    """
    assert validate.is_string(run_name)
    assert validate.is_string(name)

    # Geth the source of the data
    col1, col2, col3 = st.columns(3)
    data_source_options = ["Statistics", "Hourly results", "Production capacity", "Storage capacity (energy)", "Storage capacity (power)"]
    data_source = col1.selectbox(name.capitalize(), data_source_options)

    # Specify the aggregation options in the general scope
    aggregation_options = ["sum", "min", "max", "mean", "median", "mode", "std"]

    if data_source == "Statistics":
        # Get the type of statistic
        statistic_type_options = ["firm_lcoe", "unconstrained_lcoe", "premium", "relative_curtailment"]
        statistic_type = col2.selectbox("Type", statistic_type_options, format_func=utils.format_str, key=name)
        statistic_method = getattr(stats, statistic_type)

        # Calculate the statistics for each country and convert them into a Series
        countries = utils.read_yaml(f"../output/{run_name}/config.yaml")["countries"]
        return pd.Series(dict([(country["nuts_2"], statistic_method(run_name, countries=[country["nuts_2"]])) for country in countries]))

    if data_source == "Hourly results":
        # Get the hourly results
        all_hourly_results = utils.get_hourly_results(run_name, group="country")

        # Merge the DataFrames on a specific column
        relevant_columns = utils.find_common_columns(all_hourly_results)
        column_name = col2.selectbox("Column", relevant_columns, format_func=utils.format_column_name, key=name)
        hourly_results = utils.merge_dataframes_on_column(all_hourly_results, column_name)

        # Select the aggregation type and aggregate the hourly results
        aggregation_type = col3.selectbox("Aggregation", aggregation_options, index=3, format_func=utils.format_str, key=name)
        hourly_results_aggregated = getattr(hourly_results, aggregation_type)()

        # Return the aggregated data and formatted column name
        return hourly_results_aggregated

    if data_source == "Production capacity":
        # Get the production capacity
        production_capacity = utils.get_production_capacity(run_name, group="country")

        # Filter the production capacity on only the selected columns
        production_types = col2.multiselect("Type", production_capacity.columns, format_func=technologies.labelize, key=name)
        production_capacity = production_capacity[production_types]

        # Select the aggregation type
        aggregation_type = col3.selectbox("Aggregation", aggregation_options, format_func=utils.format_str, disabled=not production_types, key=name)

        # Aggregate and return the production capacities
        if production_types:
            production_capacity_aggregated = getattr(production_capacity, aggregation_type)(axis=1)
            return production_capacity_aggregated

    storage_capacity_match = re.search("Storage capacity \((.+)\)$", data_source)
    if storage_capacity_match:
        # Get the storage capacity
        energy_or_power = storage_capacity_match.group(1)
        storage_capacity = utils.get_storage_capacity(run_name, group="country")

        # Filter the columns on either 'energy' or 'power' and remove the energy/power label
        relevant_columns = [column for column in storage_capacity.columns if column[1] == energy_or_power]
        storage_capacity = storage_capacity[relevant_columns]
        relevant_columns = [column[0] for column in relevant_columns]
        storage_capacity.columns = relevant_columns

        # Filter the storage capacity on only the selected columns
        storage_types = col2.multiselect("Type", relevant_columns, format_func=technologies.labelize, key=name)
        storage_capacity = storage_capacity[storage_types]

        # Select the aggregation type
        aggregation_type = col3.selectbox("Aggregation", aggregation_options, format_func=utils.format_str, disabled=not storage_types, key=name)

        # Aggregate and return the storage capacities
        if storage_types:
            storage_capacity_aggregated = getattr(storage_capacity, aggregation_type)(axis=1)
            return storage_capacity_aggregated


def countries(run_name):
    """
    Show a choropleth map for all countries modeled in a run
    """
    assert validate.is_string(run_name)

    st.title("🎌 Countries")

    st.subheader("Columns")
    # Check if the data should be relative and get the numerator data
    relative = st.checkbox("Relative")
    numerator = _select_data(run_name, name="numerator")

    # Set 'data' to the numerator, else get de denominator and divide the numerator with it
    if not relative:
        data = numerator
    else:
        denominator = _select_data(run_name, name="denominator")

        if numerator is not None and denominator is not None:
            data = numerator / denominator
        else:
            data = None

    # Only show the map if the data has been selected
    if data is not None:
        st.subheader("Colorbar")
        col1, col2 = st.columns(2)

        # Get the label for the color bar
        label = col1.text_input("Label")

        # If data is still a DataFrame, convert the single column DataFrame to a series (only applicable when the 'mode' aggregator has been used)
        if validate.is_dataframe(data):
            data = data[data.columns[0]]

        # Get the units for the color bar
        units = {10 ** -9: "Billionth", 10 ** -6: "Millionth", 10 ** -3: "Thousandth", 1: "One", 10 ** 3: "Thousand", 10 ** 6: "Million", 10 ** 9: "Billion"}
        default_unit = next(unit for unit in units.keys() if (data.abs().max() < unit * 1000))
        unit = col2.select_slider("Format units", units.keys(), value=default_unit, format_func=lambda key: units[key])

        # Create and show the map
        map = chart.Map(data / unit, label=label)
        st.pyplot(map.fig)
