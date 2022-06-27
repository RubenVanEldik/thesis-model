from datetime import datetime
import gurobipy as gp

import validate


def intialize_model(config):
    """
    Initialize the model with the parameters from the config file
    """
    assert validate.is_config(config, new_config=True)

    model = gp.Model(config["name"])
    model.setParam("OutputFlag", 0)
    model.setParam("Threads", config["optimization"]["thread_count"])
    model.setParam("Method", config["optimization"]["method"])
    model.setParam("TimeLimit", (config["optimization"]["time_limit"] - datetime.now()).total_seconds())

    return model
