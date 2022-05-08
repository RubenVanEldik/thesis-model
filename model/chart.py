from matplotlib import pyplot as plt
from matplotlib import ticker as mticker
import pandas as pd
import re
import streamlit as st
import numpy as np

import colors
import validate
import utils

# Set the font for all plots to serif
plt.rcParams["font.family"] = "serif"


class Chart:
    """
    Create a matplotlib figure
    """

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


class Map:
    """
    Create a geopandas map based on a Series with country level data
    """

    fig = None
    ax = None

    def __init__(self, data, *, label=None, format_percentage=False):
        # Create the figure
        self.fig, self.ax = plt.subplots(figsize=(7, 5))
        self.ax.axis("off")
        self.ax.margins(0.02)

        # Create the color bar
        colormap = colors.colormap("blue")
        vmin = data.min()
        vmax = data[data < np.Inf].max()
        scalar_mappable = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        format = lambda x, pos: f"{x:.0%}" if format_percentage else x
        self.fig.colorbar(scalar_mappable, shrink=0.7, aspect=20, label=label, format=format)

        # Get the geopandas DataFrame and map the data to it
        map_df = utils.get_geometries_of_countries(data.index)
        map_df["data"] = map_df.index.map(data)

        # Plot the data
        map_df.plot(column="data", cmap=colormap, linewidth=0.5, ax=self.ax, edgecolor=colors.get("gray", 600))

    def save(self, filepath):
        plt.savefig(filepath, dpi=2500, bbox_inches="tight", pad_inches=0.2)


def waterfall(df, *, is_relative=False, individual_lines=True, range_area=True, ignore_zeroes=False, unity_line=False, **figure_options):
    """
    Create a waterfall chart
    """
    assert validate.is_dataframe(df)
    assert validate.is_bool(is_relative)
    assert validate.is_bool(individual_lines)
    assert validate.is_bool(range_area)
    assert validate.is_bool(ignore_zeroes)
    assert validate.is_bool(unity_line)

    # Create the figure
    chart = Chart(**figure_options)

    # Create an index ranging from 0 to 1
    num_rows = df.shape[0]
    df["index"] = [i / num_rows for i in range(num_rows)]
    df = df.set_index("index")

    # Remove all rows where all values are zero
    if ignore_zeroes:
        last_non_zero_row = df[df.max(axis=1) != 0].iloc[-1].name
        df = df[:last_non_zero_row]

    # Plot the range fill
    if range_area:
        chart.ax.fill_between(df.index, df.min(axis=1), df.max(axis=1), color=colors.get("blue", 100))
    # Plot a line for each column (country)
    if individual_lines:
        chart.ax.plot(df, color=colors.get("blue", 300), linewidth=1)
    # Plot the mean values
    chart.ax.plot(df.mean(axis=1), color=colors.get("blue", 700))
    # Plot the unity line
    if unity_line:
        chart.ax.axhline(y=1, color=colors.get(red, 600), linewidth=1)

    # Format the axes to be percentages
    chart.format_xticklabels("{:,.0%}")
    chart.format_yticklabels("{:,.0%}" if is_relative else "{:,.0f}")

    # Return the figure
    return chart.fig
