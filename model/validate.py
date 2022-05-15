import datetime
import gurobipy
import pandas as pd
import re
import shapely

import colors


def is_bidding_zone(value, *, required=True):
    if value is None:
        return not required

    return bool(re.search("^[A-Z]{2}[0-9A-Z]{2}$", value))


def is_bidding_zone_list(value, *, required=True):
    if value is None:
        return not required

    is_list = type(value) is list
    has_bidding_zone_items = all(is_bidding_zone(x) for x in value)
    return is_list and has_bidding_zone_items


def is_bool(value, *, required=True):
    if value is None:
        return not required

    return type(value) is bool


def is_climate_zone(value, *, required=True):
    if value is None:
        return not required

    return bool(re.search("^[a-z]+_[0-9A-Z]{2,3}_cf$", value))


def is_climate_zone_dict(value, *, required=True):
    if value is None:
        return not required

    is_tupledict = isinstance(value, gurobipy.tupledict)
    has_valid_keys = all(is_climate_zone(x) for x in value.keys())
    return is_tupledict and has_valid_keys


def is_color_name(value, *, required=True):
    if value is None:
        return not required

    return value in colors.list()


def is_color_value(value, *, required=True):
    if value is None:
        return not required

    return value in [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]


def is_config(value, *, required=True, new_config=False):
    if value is None:
        return not required

    if type(value) is not dict:
        return false

    has_valid_model_year = is_model_year(value["model_year"])
    has_valid_countries = is_country_obj_list(value["countries"])
    has_valid_date_range = is_date_range(value["date_range"])
    has_valid_time_limit = is_datetime(value["optimization"]["time_limit"]) and (not new_config or value["optimization"]["time_limit"] > datetime.datetime.now())
    has_valid_method = is_integer(value["optimization"]["method"], min_value=-1, max_value=6)
    has_valid_thread_count = is_integer(value["optimization"]["thread_count"], min_value=1)

    return has_valid_model_year and has_valid_countries and has_valid_date_range and has_valid_time_limit and has_valid_method


def is_country_code(value, *, required=True, type):
    if value is None:
        return not required

    if type == "nuts_2":
        return bool(re.search("^[A-Z]{2}$", value))
    if type == "alpha_3":
        return bool(re.search("^[A-Z]{3}$", value))
    return False


def is_country_code_list(value, *, required=True, type):
    if value is None:
        return not required

    is_list = is_list_like(value)
    has_valid_items = all(is_country_code(code, type=type) for code in value)
    return is_list and has_valid_items


def is_country_obj(value, *, required=True):
    if value is None:
        return not required

    is_dict = type(value) is dict
    has_required_keys = bool(value["name"] and value["zones"])
    return is_dict and has_required_keys


def is_country_obj_list(value, *, required=True):
    if value is None:
        return not required

    is_list = type(value) is list
    has_items = len(value) > 0
    has_valid_items = all(is_country_obj(x) for x in value)
    return is_list and has_items and has_valid_items


def is_dataframe(value, *, required=True, column_validator=None):
    if value is None:
        return not required

    if column_validator and not all(column_validator(column_name) for column_name in value.columns):
        return False

    return isinstance(value, pd.DataFrame)


def is_dataframe_dict(value, *, required=True):
    if value is None:
        return not required

    is_dict = type(value) is dict
    has_valid_items = all(is_dataframe(value[x]) for x in value)

    return is_dict and has_valid_items


def is_date(value, *, required=True):
    if value is None:
        return not required

    return type(value) is datetime.date


def is_datetime(value, *, required=True):
    if value is None:
        return not required

    return type(value) is datetime.datetime


def is_dict(value, *, required=True):
    if value is None:
        return not required

    return type(value) is dict


def is_dict_or_list(value, *, required=True):
    if value is None:
        return not required

    is_list = type(value) is list
    is_dict = type(value) is dict
    return is_list or is_dict


def is_aggregation_level(value, *, required=True):
    if value is None:
        return not required

    return value in ["all", "country"]


def is_hourly_data_row(value, *, required=True):
    if value is None:
        return not required

    is_series = is_series(value)
    includes_demand = any(x.startswith("demand_") for x in value.index)
    includes_pv = any(x.startswith("pv_") for x in value.index)
    includes_onshore = any(x.startswith("onshore_") for x in value.index)
    return is_series and includes_demand and includes_pv and includes_onshore


def is_hourly_results_row(value, *, required=True):
    if value is None:
        return not required

    is_series = is_series(value)
    includes_demand = any(x.startswith("demand_") for x in value.index)
    includes_production = any(x.startswith("production_") for x in value.index)
    includes_net_storage_flow = any(x.startswith("net_storage_flow") for x in value.index)
    return is_series and includes_demand and includes_production and includes_net_storage_flow


def is_date_range(value, *, required=True):
    if value is None:
        return not required

    is_dict = type(value) is dict
    has_valid_start_date = value["start"] and type(value["start"]) is datetime.date
    has_valid_end_date = value["end"] and type(value["end"]) is datetime.date
    return is_dict and has_valid_start_date and has_valid_end_date


def is_filepath(value, *, required=True, suffix=None):
    if value is None:
        return not required

    is_valid_path = bool(re.search("([0-9a-zA-Z_\.]+)+\.[a-z]", value))
    has_valid_suffix = not suffix or bool(re.search(f"{suffix}$", value))
    return is_valid_path and has_valid_suffix


def is_float(value, *, required=True, min_value=None, max_value=None):
    if value is None:
        return not required

    is_float = type(value) is float
    valid_float = (min_value is None or value >= min_value) and (max_value is None or value <= max_value)
    return is_float and valid_float


def is_func(value, *, required=True):
    if value is None:
        return not required

    return callable(value)


def is_interconnection_type(value, *, required=True):
    if value is None:
        return not required

    return value in ["hvac", "hvdc"]


def is_interconnection_direction(value, *, required=True):
    if value is None:
        return not required

    return value in ["import", "export"]


def is_integer(value, *, required=True, min_value=None, max_value=None):
    if value is None:
        return not required

    is_integer = type(value) is int
    valid_integer = (min_value is None or value >= min_value) and (max_value is None or value <= max_value)
    return is_integer and valid_integer


def is_list_like(value, *, required=True):
    if value is None:
        return not required

    return pd.api.types.is_list_like(value)


def is_model(value, *, required=True):
    if value is None:
        return not required

    return isinstance(value, gurobipy.Model)


def is_model_year(value, *, required=True):
    if value is None:
        return not required

    return value == 2025 or value == 2030


def is_number(value, *, required=True, min_value=None, max_value=None):
    if value is None:
        return not required

    return is_float(value, min_value=min_value, max_value=max_value) or is_integer(value, min_value=min_value, max_value=max_value)


def is_point(value, *, required=True):
    if value is None:
        return not required

    return type(value) is shapely.geometry.point.Point


def is_sensitivity_config(value, *, required=True):
    if value is None:
        return not required

    is_dict = type(value) is dict
    has_valid_steps = all(type(key) is str and type(value) is float for key, value in value["steps"].items())
    has_valid_variables = len(value["variables"]) and all(type(variable) is str for variable in value["variables"])

    return is_dict and has_valid_steps and has_valid_variables


def is_series(value, *, required=True):
    if value is None:
        return not required

    return type(value) is pd.core.series.Series


def is_string(value, *, required=True, min_length=0):
    if value is None:
        return not required

    is_string = type(value) is str
    has_valid_length = len(value) >= min_length

    return is_string and has_valid_length


def is_technology(value, *, required=True):
    if value is None:
        return not required

    production_technologies = ["pv", "onshore", "offshore"]
    storage_technologies = ["lion", "hydrogen"]
    return value in production_technologies or value in storage_technologies


def is_technology_scenario(value, *, required=True):
    if value is None:
        return not required

    return value in ["conservative", "moderate", "advanced"]


def is_technology_type(value, *, required=True):
    if value is None:
        return not required

    return value in ["production", "storage"]


def is_variable(value, *, required=True):
    if value is None:
        return not required

    return isinstance(value, gurobipy.Var)


def is_variable_tupledict(value, *, required=True):
    if value is None:
        return not required

    is_tupledict = isinstance(value, gurobipy.tupledict)
    has_valid_values = all(is_variable(x) for x in value.values())
    return is_tupledict and has_valid_values
