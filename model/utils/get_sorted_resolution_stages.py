import pandas as pd

import validate


def get_sorted_resolution_stages(config, descending=False):
    """
    Get the resolution stages and sort them either ascending or descending
    """
    assert validate.is_config(config)
    assert validate.is_bool(descending)

    resolution_stages = config["time_discretization"]["resolution_stages"]
    return sorted(resolution_stages, key=lambda resolution: pd.Timedelta(resolution).total_seconds(), reverse=descending)
