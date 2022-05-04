from matplotlib.colors import LinearSegmentedColormap

import validate


def gray(value):
    if value == 50:
        return "#FAFAFA"
    if value == 100:
        return "#F5F5F5"
    if value == 200:
        return "#E5E5E5"
    if value == 300:
        return "#D4D4D4"
    if value == 400:
        return "#A3A3A3"
    if value == 500:
        return "#737373"
    if value == 600:
        return "#525252"
    if value == 700:
        return "#404040"
    if value == 800:
        return "#262626"
    if value == 900:
        return "#171717"
    return "#B91C1C"  # Red


def blue(value):
    if value == 50:
        return "#EFF6FF"
    if value == 100:
        return "#DBEAFE"
    if value == 200:
        return "#BFDBFE"
    if value == 300:
        return "#93C5FD"
    if value == 400:
        return "#60A5FA"
    if value == 500:
        return "#3B82F6"
    if value == 600:
        return "#2563EB"
    if value == 700:
        return "#1D4ED8"
    if value == 800:
        return "#1E40AF"
    if value == 900:
        return "#1E3A8A"
    return "#B91C1C"  # Red


def red(value):
    if value == 50:
        return "#FEF2F2"
    if value == 100:
        return "#FEE2E2"
    if value == 200:
        return "#FECACA"
    if value == 300:
        return "#FCA5A5"
    if value == 400:
        return "#F87171"
    if value == 500:
        return "#EF4444"
    if value == 600:
        return "#DC2626"
    if value == 700:
        return "#B91C1C"
    if value == 800:
        return "#991B1B"
    if value == 900:
        return "#7F1D1D"
    return "#737373"  # Gray


def colormap(color1, color2=None):
    """
    Return a colormap based on one or two colors
    """
    assert validate.is_color(color1)
    assert validate.is_color(color2, required=False)

    # Create a list with colors and a name for the colormap
    if color2 is None:
        name = f"model:{color1}"
        color_list = [eval(color1)(value) for value in range(100, 1000, 100)]
    else:
        name = f"model:{color1}-{color2}"
        color_list1 = [eval(color1)(value) for value in range(900, 0, -100)]
        color_list2 = [eval(color2)(value) for value in range(100, 1000, 100)]
        color_list = color_list1 + color_list2

    # Return the colormap
    colormap = LinearSegmentedColormap.from_list(name, color_list)
    return colormap
