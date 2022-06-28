import streamlit as st

import utils
import validate


def firm_lcoe(run_name, resolution, *, countries=None):
    """
    Calculate the firm LCOE for a specific run
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # Get the capacities and demand
    production_capacity = utils.get_production_capacity(run_name, resolution, countries=countries)
    storage_capacity = utils.get_storage_capacity(run_name, resolution, countries=countries)
    temporal_results = utils.get_temporal_results(run_name, resolution, countries=countries)
    temporal_demand = utils.merge_dataframes_on_column(temporal_results, "demand_MW")
    temporal_export = utils.merge_dataframes_on_column(temporal_results, "net_export_MW")
    temporal_net_demand = temporal_demand + temporal_export
    config = utils.read_yaml(f"./output/{run_name}/config.yaml")

    # Return the LCOE
    return utils.calculate_lcoe(production_capacity, storage_capacity, temporal_net_demand, config=config)


def unconstrained_lcoe(run_name, resolution, *, countries=None):
    """
    Calculate the unconstrained_lcoe LCOE for a specific run
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # Get the capacities and demand
    production_capacity = utils.get_production_capacity(run_name, resolution, countries=countries)
    storage_capacity = utils.get_storage_capacity(run_name, resolution, countries=countries)
    temporal_results = utils.get_temporal_results(run_name, resolution, countries=countries)
    temporal_demand = utils.merge_dataframes_on_column(temporal_results, "production_total_MW")
    config = utils.read_yaml(f"./output/{run_name}/config.yaml")

    # Return the LCOE
    return utils.calculate_lcoe(production_capacity, storage_capacity, temporal_demand, config=config)


def premium(run_name, resolution, *, countries=None):
    """
    Calculate the firm kWh premium
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # Get the capacities and demand
    firm_lcoe_result = firm_lcoe(run_name, resolution, countries=countries)
    unconstrained_lcoe_result = unconstrained_lcoe(run_name, resolution, countries=countries)

    # Return the firm kWh premium
    return firm_lcoe_result / unconstrained_lcoe_result


def relative_curtailment(run_name, resolution, *, countries=None):
    """
    Calculate the relative curtailment
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    temporal_results = utils.get_temporal_results(run_name, resolution, group="all", countries=countries)
    return temporal_results.curtailed_MW.sum() / temporal_results.production_total_MW.sum()


def production_capacity(run_name, resolution, *, countries=None):
    """
    Return a dictionary with the production capacity per production type
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    production_capacity = utils.get_production_capacity(run_name, resolution, group="all", countries=countries)
    return production_capacity.to_dict()


def storage_capacity(run_name, resolution, *, type, countries=None):
    """
    Return a dictionary with the storage capacity per storage type for either 'energy' or 'power'
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)
    assert validate.is_string(type)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    storage_capacity = utils.get_storage_capacity(run_name, resolution, group="all", countries=countries)

    # Return an empty dictionary if there is no storage
    if storage_capacity is None:
        return {}

    return storage_capacity[type].to_dict()
