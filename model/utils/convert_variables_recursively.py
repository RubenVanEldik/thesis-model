import gurobipy as gp
import pandas as pd

import validate


def convert_variables_recursively(data):
    """
    Store a dictionary or list as .yaml file
    """
    if type(data) is dict:
        for key, value in data.items():
            data[key] = convert_variables_recursively(value)
        return data
    elif type(data) is list:
        return [convert_variables_recursively(value) for value in data]
    elif type(data) is pd.core.frame.DataFrame:
        return data.applymap(convert_variables_recursively)
    elif type(data) is gp.Var:
        return data.X
    elif type(data) in [gp.LinExpr, gp.QuadExpr]:
        return data.getValue()
    return data
