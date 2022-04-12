from matplotlib import pyplot as plt
import pandas as pd
import re

import color
import validate

# Set the font for all plots to serif
plt.rcParams["font.family"] = "serif"


def waterfall(dfs, *, column):
    """
    Create a waterfall chart
    """
    assert validate.is_dataframe_dict(dfs)
    assert validate.is_string(column)

    # Create a new DataFrame with only the relevant column and all values sorted
    df = pd.DataFrame()
    for key in dfs:
        col = dfs[key].sort_values(column, ascending=False)[column]
        df[key] = col.tolist()

    # Create an index ranging from 0 to 1
    num_rows = df.shape[0]
    df["index"] = [i / num_rows for i in range(num_rows)]
    df = df.set_index("index")

    # Get the weighted average of the columns
    mean = df.apply(lambda column: column.mean(), axis=1)
    mean_rel = mean / mean.max()

    # Calculate the min and max values
    df_rel = df / df.max()
    min_rel = df_rel.apply(lambda row: row.min(), axis=1)
    max_rel = df_rel.apply(lambda row: row.max(), axis=1)

    # Create the figure
    fig, ax = plt.subplots(figsize=(7, 5))

    # Add the line and fill
    ax.plot(mean_rel, color=color.blue(700))
    ax.fill_between(df.index, min_rel, max_rel, color=color.blue(200))

    # Set the axes' labels
    ax.set(xlabel="Time (%)")
    column_label = re.search("(.+)_MWh", column).group(1).replace("_", " ").capitalize()
    ax.set(ylabel=f"{column_label} (%)")

    # Format the axes to be percentages
    ax.set_xticklabels(["{:,.0%}".format(x) for x in ax.get_xticks()])
    ax.set_yticklabels(["{:,.0%}".format(x) for x in ax.get_yticks()])

    # Return the figure
    return fig
