import pandas as pd
import re
import streamlit as st

import chart
import stats
import utils
import validate


def _select_data(output_directory, resolution, *, name):
    """
    Select the source of the data and the specific columns and aggregation type
    """
    assert validate.is_directory_path(output_directory)
    assert validate.is_resolution(resolution)
    assert validate.is_string(name)

    # Get the source of the data
    col1, col2 = st.sidebar.columns(2)
    data_source_options = ["Statistics", "Temporal results", "Production capacity", "Storage capacity (energy)", "Storage capacity (power)"]
    data_source = col1.selectbox(name.capitalize(), data_source_options)

    if data_source == "Statistics":
        # Get the type of statistic
        statistic_type_options = ["firm_lcoe", "unconstrained_lcoe", "premium", "relative_curtailment", "self_sufficiency"]
        statistic_type = col2.selectbox("Type", statistic_type_options, format_func=utils.format_str, key=name)
        statistic_method = getattr(stats, statistic_type)

        # Calculate the statistics for each country and convert them into a Series
        country_codes = utils.read_yaml(output_directory / "config.yaml")["country_codes"]
        return pd.Series({country_code: statistic_method(output_directory, resolution, country_codes=[country_code]) for country_code in country_codes})

    if data_source == "Temporal results":
        # Get the temporal results
        all_temporal_results = utils.get_temporal_results(output_directory, resolution, group="country")

        # Merge the DataFrames on a specific column
        relevant_columns = utils.find_common_columns(all_temporal_results)
        column_name = col2.selectbox("Column", relevant_columns, format_func=utils.format_column_name, key=name)
        temporal_results = utils.merge_dataframes_on_column(all_temporal_results, column_name)

        # Average values of the selected temporal column
        return temporal_results.mean()

    if data_source == "Production capacity":
        # Get the production capacity
        production_capacity = utils.get_production_capacity(output_directory, resolution, group="country")

        # Get the specific technologies
        selected_production_types = col2.multiselect("Type", production_capacity.columns, format_func=utils.format_technology, key=name)

        # Return the sum the capacities of all selected technologies
        if selected_production_types:
            return production_capacity[selected_production_types].sum(axis=1)

    storage_capacity_match = re.search("Storage capacity \((.+)\)$", data_source)
    if storage_capacity_match:
        energy_or_power = storage_capacity_match.group(1)

        # Get the storage capacity
        storage_capacity = utils.get_storage_capacity(output_directory, resolution, group="country")

        # Create a DataFrame with all storage (energy or power) capacities
        storage_capacity_aggregated = None
        for country_code in storage_capacity:
            if storage_capacity_aggregated is None:
                storage_capacity_aggregated = pd.DataFrame(columns=storage_capacity[country_code].index)
            storage_capacity_aggregated.loc[country_code] = storage_capacity[country_code][energy_or_power]

        # Get the specific technologies
        selected_storage_types = col2.multiselect("Type", storage_capacity_aggregated.columns, format_func=utils.format_technology, key=name)

        # Return the sum the capacities of all selected technologies
        if selected_storage_types:
            return storage_capacity_aggregated[selected_storage_types].sum(axis=1)


def countries(output_directory, resolution):
    """
    Show a choropleth map for all countries modeled in a run
    """
    assert validate.is_directory_path(output_directory)
    assert validate.is_resolution(resolution)

    st.title("???? Countries")

    st.sidebar.header("Options")

    # Check if the data should be relative and get the numerator data
    relative = st.sidebar.checkbox("Relative")
    numerator = _select_data(output_directory, resolution, name="numerator")

    # Set 'data' to the numerator, else get de denominator and divide the numerator with it
    if not relative:
        data = numerator
    else:
        denominator = _select_data(output_directory, resolution, name="denominator")

        if numerator is not None and denominator is not None:
            data = numerator / denominator
        else:
            data = None

    # Only show the map if the data has been selected
    if data is not None:
        # Get the label for the color bar
        label = st.sidebar.text_input("Label")

        # If data is still a DataFrame, convert the single column DataFrame to a series (only applicable when the 'mode' aggregator has been used)
        if validate.is_dataframe(data):
            data = data[data.columns[0]]

        # Get the units for the color bar
        units = {10 ** -9: "Billionth", 10 ** -6: "Millionth", 10 ** -3: "Thousandth", 1: "One", 10 ** 3: "Thousand", 10 ** 6: "Million", 10 ** 9: "Billion"}
        unit = st.sidebar.select_slider("Format units", units.keys(), value=1, format_func=lambda key: units[key])

        # Create and show the map
        map = chart.Map(data / unit, label=label)
        st.pyplot(map.fig)
