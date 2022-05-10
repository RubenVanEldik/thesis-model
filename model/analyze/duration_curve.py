import re
import streamlit as st

import chart
import utils
import validate


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
