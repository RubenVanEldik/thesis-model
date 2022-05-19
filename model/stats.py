import streamlit as st

import utils
import validate


def firm_lcoe(run_name, *, countries=None):
    """
    Calculate the firm LCOE for a specific run
    """
    assert validate.is_string(run_name)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # Get the capacities and demand
    production_capacity = utils.get_production_capacity(run_name, countries=countries)
    storage_capacity = utils.get_storage_capacity(run_name, countries=countries)
    hourly_results = utils.get_hourly_results(run_name, countries=countries)
    hourly_demand = utils.merge_dataframes_on_column(hourly_results, "demand_MWh")
    config = utils.read_yaml(f"./output/{run_name}/config.yaml")

    # Return the LCOE
    return utils.calculate_lcoe(production_capacity, storage_capacity, hourly_demand, config=config)


def unconstrained_lcoe(run_name, *, countries=None):
    """
    Calculate the unconstrained_lcoe LCOE for a specific run
    """
    assert validate.is_string(run_name)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # Get the capacities and demand
    production_capacity = utils.get_production_capacity(run_name, countries=countries)
    storage_capacity = utils.get_storage_capacity(run_name, countries=countries)
    hourly_results = utils.get_hourly_results(run_name, countries=countries)
    hourly_demand = utils.merge_dataframes_on_column(hourly_results, "production_total_MWh")
    config = utils.read_yaml(f"./output/{run_name}/config.yaml")

    # Return the LCOE
    return utils.calculate_lcoe(production_capacity, storage_capacity, hourly_demand, config=config)


def premium(run_name, *, countries=None):
    """
    Calculate the firm kWh premium
    """
    assert validate.is_string(run_name)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # Get the capacities and demand
    firm_lcoe_result = firm_lcoe(run_name, countries=countries)
    unconstrained_lcoe_result = unconstrained_lcoe(run_name, countries=countries)

    # Return the firm kWh premium
    return firm_lcoe_result / unconstrained_lcoe_result


def relative_curtailment(run_name, *, countries=None):
    """
    Calculate the relative curtailment
    """
    assert validate.is_string(run_name)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    hourly_results = utils.get_hourly_results(run_name, group="all", countries=countries)
    return hourly_results.curtailed_MWh.sum() / hourly_results.production_total_MWh.sum()


def production_capacity(run_name, *, countries=None):
    """
    Return a dictionary with the production capacity per production type
    """
    assert validate.is_string(run_name)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    production_capacity = utils.get_production_capacity(run_name, group="all", countries=countries)
    return production_capacity.to_dict()


def storage_capacity(run_name, *, type, countries=None):
    """
    Return a dictionary with the storage capacity per storage type for either 'energy' or 'power'
    """
    assert validate.is_string(run_name)
    assert validate.is_string(type)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    storage_capacity = utils.get_storage_capacity(run_name, group="all", countries=countries)

    # Return an empty dictionary if there is no storage
    if not storage_capacity:
        return {}

    storage_capacity = storage_capacity[storage_capacity.index.get_level_values(1) == type]
    storage_capacity = storage_capacity.droplevel(1)
    return storage_capacity.to_dict()
