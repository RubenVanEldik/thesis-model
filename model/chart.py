from matplotlib import pyplot as plt
from matplotlib import ticker as mticker
import pandas as pd
import re
import streamlit as st

import color
import validate

# Set the font for all plots to serif
plt.rcParams["font.family"] = "serif"


class Chart:
    fig = None
    ax = None

    def __init__(self, *, xlabel, ylabel, xscale="linear", yscale="linear"):
        # Create the figure
        self.fig, self.ax = plt.subplots(figsize=(7, 5))

        # Set the axes' labels and scale
        self.ax.set(xlabel=xlabel)
        self.ax.set(ylabel=ylabel)
        self.ax.set_xscale(xscale)
        self.ax.set_yscale(yscale)

    def format_xticklabels(self, label):
        ticks_loc = self.ax.get_xticks().tolist()
        self.ax.xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        xticks = self.ax.get_xticks()
        self.ax.set_xticklabels([label.format(tick) for tick in xticks])

    def format_yticklabels(self, label):
        ticks_loc = self.ax.get_yticks().tolist()
        self.ax.yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        yticks = self.ax.get_yticks()
        self.ax.set_yticklabels([label.format(tick) for tick in yticks])

    def save(self, filepath):
        plt.savefig(filepath, dpi=250, bbox_inches="tight", pad_inches=0.2)


@st.experimental_memo
def merge_dataframes_on_column(dfs, column, *, ignore_zeroes=False):
    """
    Create one DataFrame from a dictionary of DataFrames by selecting only one column per DataFrame
    """
    assert validate.is_dataframe_dict(dfs)
    assert validate.is_string(column)

    df = pd.DataFrame()
    for key in dfs:
        col = dfs[key].sort_values(column, ascending=False)[column]
        df[key] = col.tolist()

    # Remove all rows where all values are zero
    if ignore_zeroes:
        last_non_zero_row = df[df.max(axis=1) != 0].iloc[-1].name
        df = df[:last_non_zero_row]

    # Create an index ranging from 0 to 1
    num_rows = df.shape[0]
    df["index"] = [i / num_rows for i in range(num_rows)]
    df = df.set_index("index")
    return df


def waterfall(dfs, *, numerator, denominator=None, individual_lines=True, range_area=True, ignore_zeroes=False, unity_line=False, **figure_options):
    """
    Create a waterfall chart
    """
    assert validate.is_dataframe_dict(dfs)
    assert validate.is_string(numerator)
    assert validate.is_string(denominator, required=False)
    assert validate.is_bool(individual_lines)
    assert validate.is_bool(range_area)
    assert validate.is_bool(unity_line)

    # Create two new DataFrames with only the numerator/denominator column and all values sorted
    numerator_df = merge_dataframes_on_column(dfs, numerator, ignore_zeroes=ignore_zeroes)
    if denominator is None:
        denominator_df = pd.DataFrame(1, index=numerator_df.index, columns=numerator_df.columns)
    else:
        denominator_df = merge_dataframes_on_column(dfs, denominator, ignore_zeroes=ignore_zeroes)

    # Create the figure
    chart = Chart(**figure_options)

    # Plot the range fill
    if range_area:
        df_rel = numerator_df / denominator_df.max()
        relative_min = df_rel.min(axis=1)
        relative_max = df_rel.max(axis=1)
        chart.ax.fill_between(numerator_df.index, relative_min, relative_max, color=color.blue(100))
    # Plot a line for each column (country)
    if individual_lines:
        for column_name in numerator_df:
            relative_column = numerator_df[column_name] / denominator_df[column_name].max()
            chart.ax.plot(relative_column, color=color.blue(300), linewidth=1)
    # Plot the mean values
    relative_mean = numerator_df.mean(axis=1) / denominator_df.mean(axis=1).max()
    chart.ax.plot(relative_mean, color=color.blue(700))
    # Plot the unity line
    if unity_line:
        chart.ax.axhline(y=1, color=color.red(600), linewidth=1)

    # Format the axes to be percentages
    chart.format_xticklabels("{:,.0%}")
    chart.format_yticklabels("{:,.0f}" if denominator is None else "{:,.0%}")

    # Return the figure
    return chart.fig
