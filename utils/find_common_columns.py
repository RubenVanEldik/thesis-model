import validate


def find_common_columns(dfs):
    """
    Return a list of the columns that appear in all DataFrames
    """
    assert validate.is_dataframe_dict(dfs)

    common_columns = None
    for df in dfs.values():
        if common_columns is None:
            common_columns = df.columns
        else:
            common_columns = common_columns & df.columns

    return list(common_columns)
