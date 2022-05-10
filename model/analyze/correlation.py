import pandas as pd
import streamlit as st

import chart
import colors
import utils
import validate


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
