import streamlit as st

import utils
import validate


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
