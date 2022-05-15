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

    def set_x_limits(self, x_min, x_max):
        self.ax.set_xlim([x_min, x_max])

    def set_y_limits(self, y_min, y_max):
        self.ax.set_ylim([y_min, y_max])

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
