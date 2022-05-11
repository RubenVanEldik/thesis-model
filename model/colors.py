import streamlit as st
from matplotlib.colors import LinearSegmentedColormap

import validate
import utils


def get(color, value):
    """
    Return the HEX value for a specific color and value
    """
    assert validate.is_color_name(color)
    assert validate.is_color_value(value)

    colors = utils.read_csv("./model/colors.csv", index_col=0)
    return colors.loc[value, color]


def list():
    """
    Return a list of all available colors
    """
    colors = utils.read_csv("./model/colors.csv", index_col=0)
    return colors.columns.tolist()


def colormap(color1, color2=None):
    """
    Return a colormap based on one or two colors
    """
    assert validate.is_color_name(color1)
    assert validate.is_color_name(color2, required=False)

    # Create a list with colors and a name for the colormap
    if color2 is None:
        name = f"model:{color1}"
        color_list = [get(color1, value) for value in range(100, 1000, 100)]
    else:
        name = f"model:{color1}-{color2}"
        color_list1 = [get(color1, value) for value in range(900, 0, -100)]
        color_list2 = [get(color2, value) for value in range(100, 1000, 100)]
        color_list = color_list1 + color_list2

    # Return the colormap
    colormap = LinearSegmentedColormap.from_list(name, color_list)
    return colormap
