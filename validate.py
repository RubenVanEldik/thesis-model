import datetime
import gurobipy
import pandas as pd
import re
import shapely

import colors


def is_bidding_zone(value, *, required=True):
    if value is None:
        return not required

    return bool(re.search("^[A-Z]{2}[0-9a-zA-Z]{2}$", value))


def is_bidding_zone_list(value, *, required=True):
    if value is None:
        return not required

    if type(value) is not list:
        return False

    return all(is_bidding_zone(x) for x in value)


def is_bool(value, *, required=True):
    if value is None:
        return not required

    return type(value) is bool


def is_climate_zone(value, *, required=True):
    if value is None:
        return not required

    return bool(re.search("^[a-z]+_[0-9A-Z]{2,3}_cf$", value))


def is_bidding_zone_dict(value, *, required=True):
    if value is None:
        return not required

    if not type(value) is dict and not isinstance(value, gurobipy.tupledict):
        return False

    return all(is_bidding_zone(x) for x in value.keys())


def is_color_name(value, *, required=True):
    if value is None:
        return not required

    return value in colors.list()


def is_color_value(value, *, required=True):
    if value is None:
        return not required

    return value in [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]


def is_config(value, *, required=True):
    if value is None:
        return not required

    if type(value) is not dict:
        return False

    if not is_directory_path(value.get("name")):
        return False
    if not is_model_year(value.get("model_year")):
        return False
    if not is_country_obj_list(value.get("countries")):
        return False
    if not is_date_range(value.get("date_range")):
        return False
    if not value.get("time_discretization"):
        return False
    if not is_resolution_stages(value["time_discretization"].get("resolution_stages")):
        return False
    if not value.get("optimization"):
        return False
    if not is_integer(value["optimization"].get("method"), min_value=-1, max_value=6):
        return False
    if not is_integer(value["optimization"].get("thread_count"), min_value=1):
        return False

    return True


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

    if not is_list_like(value):
        return False

    return all(is_country_code(code, type=type) for code in value)


def is_country_obj(value, *, required=True):
    if value is None:
        return not required

    if not type(value) is dict:
        return False

    return bool(value["name"] and value["bidding_zones"])


def is_country_obj_list(value, *, required=True):
    if value is None:
        return not required

    if not is_list_like(value) or not len(value) > 0:
        return False

    return all(is_country_obj(x) for x in value)


def is_dataframe(value, *, required=True, column_validator=None):
    if value is None:
        return not required

    if not isinstance(value, pd.DataFrame):
        return False

    if column_validator:
        return all(column_validator(column_name) for column_name in value.columns)

    return True


def is_dataframe_dict(value, *, required=True):
    if value is None:
        return not required

    if not type(value) is dict:
        return False

    return all(is_dataframe(value[x]) for x in value)


def is_date(value, *, required=True):
    if value is None:
        return not required

    return type(value) is datetime.date


def is_datetime(value, *, required=True):
    if value is None:
        return not required

    return type(value) is datetime.datetime


def is_datetime_index(value, *, required=True):
    if value is None:
        return not required

    return type(value) is pd.core.indexes.datetimes.DatetimeIndex


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


def is_directory_path(value, *, required=True):
    if value is None:
        return not required

    return bool(re.search("^[^\n\r\t\0]+$", value))


def is_aggregation_level(value, *, required=True):
    if value is None:
        return not required

    return value in ["all", "country"]


def is_date_range(value, *, required=True):
    if value is None:
        return not required

    if not type(value) is dict:
        return False

    has_valid_start_date = value["start"] and type(value["start"]) is datetime.date
    has_valid_end_date = value["end"] and type(value["end"]) is datetime.date
    return has_valid_start_date and has_valid_end_date


def is_filepath(value, *, required=True, suffix=None):
    if value is None:
        return not required

    is_valid_path = bool(re.search("^[^\n\r\t\0]+\.[a-z]+$", value))
    has_valid_suffix = not suffix or bool(re.search(f"{suffix}$", value))
    return is_valid_path and has_valid_suffix


def is_filepath_list(value, *, required=True, suffix=None):
    if value is None:
        return not required

    if not is_list_like(value):
        return False

    return all(is_filepath(filepath, suffix=suffix) for filepath in value)


def is_float(value, *, required=True, min_value=None, max_value=None):
    if value is None:
        return not required

    if not type(value) is float:
        return False

    if min_value is not None and value < min_value:
        return False

    if max_value is not None and value > max_value:
        return False

    return True


def is_func(value, *, required=True):
    if value is None:
        return not required

    return callable(value)


def is_interconnection_tuple(value, *, required=True):
    if value is None:
        return not required

    if type(value) is not tuple or len(value) != 2:
        return False

    return is_bidding_zone(value[0]) and (is_bidding_zone(value[1]) or bool(re.search("^(gross|net)_(ex|im)port_limit$", value[1])))


def is_interconnection_type(value, *, required=True):
    if value is None:
        return not required

    return value in ["hvac", "hvdc", "limits"]


def is_interconnection_direction(value, *, required=True):
    if value is None:
        return not required

    return value in ["import", "export"]


def is_integer(value, *, required=True, min_value=None, max_value=None):
    if value is None:
        return not required

    if not type(value) is int:
        return False

    if min_value is not None and value < min_value:
        return False

    if max_value is not None and value > max_value:
        return False

    return True


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


def is_resolution(value, *, required=True):
    if value is None:
        return not required

    if not is_string(value):
        return False

    try:
        pd.tseries.frequencies.to_offset(value)
        return True
    except ValueError:
        return False


def is_resolution_stages(value, *, required=True):
    if value is None:
        return not required

    if type(value) is not list or len(value) == 0:
        return False

    return all(is_resolution(resolution) for resolution in value)


def is_sensitivity_config(value, *, required=True):
    if value is None:
        return not required

    if not type(value) is dict:
        return False

    has_valid_steps = all(type(key) is str and type(value) is float for key, value in value["steps"].items())
    has_valid_variables = len(value["variables"]) and all(type(variable) is str for variable in value["variables"])
    return has_valid_steps and has_valid_variables


def is_series(value, *, required=True):
    if value is None:
        return not required

    return type(value) is pd.core.series.Series


def is_string(value, *, required=True, min_length=0):
    if value is None:
        return not required

    if not type(value) is str:
        return False

    return len(value) >= min_length


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


def is_url(value, *, required=True):
    if value is None:
        return not required

    url_regex = '^(ftp|https?):\/\/[^ "]+\.\w{2,}'
    return bool(re.search(url_regex, value))


def is_variable(value, *, required=True):
    if value is None:
        return not required

    return isinstance(value, gurobipy.Var)


def is_variable_tupledict(value, *, required=True):
    if value is None:
        return not required

    if not isinstance(value, gurobipy.tupledict):
        return False

    return all(is_variable(x) for x in value.values())
