import datetime
import gurobipy
import pandas as pd
import re


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


def is_config(value, *, required=True):
    if value is None:
        return not required

    is_dict = type(value) is dict
    has_valid_model_year = is_model_year(value["model_year"])
    has_valid_countries = is_country_obj_list(value["countries"])
    has_valid_date_range = is_date_range(value["date_range"])
    has_valid_time_limit = is_datetime(value["optimization_time_limit"]) and value["optimization_time_limit"] > datetime.datetime.now()
    has_valid_method = is_optimization_method(value["optimization_method"])

    return is_dict and has_valid_model_year and has_valid_countries and has_valid_date_range and has_valid_time_limit and has_valid_method


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


def is_date(value, *, required=True):
    if value is None:
        return not required

    return type(value) is datetime.date


def is_datetime(value, *, required=True):
    if value is None:
        return not required

    return type(value) is datetime.datetime


def is_dict_or_list(value, *, required=True):
    if value is None:
        return not required

    is_list = type(value) is list
    is_dict = type(value) is dict
    return is_list or is_dict


def is_hourly_data_row(value, *, required=True):
    if value is None:
        return not required

    is_series = type(value) is pd.core.series.Series
    includes_demand = any(x.startswith("demand_") for x in value.index)
    includes_pv = any(x.startswith("pv_") for x in value.index)
    includes_onshore = any(x.startswith("onshore_") for x in value.index)
    return is_series and includes_demand and includes_pv and includes_onshore


def is_hourly_results_row(value, *, required=True):
    if value is None:
        return not required

    is_series = type(value) is pd.core.series.Series
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


def is_model(value, *, required=True):
    if value is None:
        return not required

    return isinstance(value, gurobipy.Model)


def is_model_year(value, *, required=True):
    if value is None:
        return not required

    return value == 2025 or value == 2030


def is_optimization_method(value, *, required=True):
    if value is None:
        return not required

    is_integer = type(value) is int
    has_valid_value = -1 <= value <= 5

    return is_integer and has_valid_value


def is_technology(value, *, required=True):
    if value is None:
        return not required

    production_technologies = ["pv", "onshore", "offshore"]
    storage_technologies = ["lion"]
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
