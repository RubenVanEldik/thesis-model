import datetime
import pandas as pd
import gurobipy
import re


def is_bidding_zone(value, *, required=True):
    if value is None:
        return not required

    return bool(re.search("^[A-Z]{2}[0-9A-Z]{2}$", value))


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
    has_valid_items = all(is_country_obj(x) for x in value)
    return is_list and has_valid_items


def is_data_row(value, *, required=True):
    if value is None:
        return not required

    is_series = type(value) is pd.core.series.Series
    includes_demand = any(x.startswith("demand_") for x in value.index)
    includes_pv = any(x.startswith("pv_") for x in value.index)
    includes_onshore = any(x.startswith("onshore_") for x in value.index)
    return is_series and includes_demand and includes_pv and includes_onshore


def is_date_range(value, *, required=True):
    if value is None:
        return not required

    is_tuple = type(value) is tuple and len(value) == 2
    has_datetime_items = all(type(x) is datetime.date for x in value)
    return is_tuple and has_datetime_items


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


def is_model(value, *, required=True):
    if value is None:
        return not required

    return isinstance(value, gurobipy.Model)


def is_model_year(value, *, required=True):
    if value is None:
        return not required

    return value == 2025 or value == 2030


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