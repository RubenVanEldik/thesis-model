import streamlit as st

import lcoe
import utils
import validate


def firm_lcoe(run_name):
    """
    Calculate the firm LCOE for a specific run
    """
    assert validate.is_string(run_name)

    # Get the capacities and demand
    production_capacity = utils.get_production_capacity(run_name)
    storage_capacity = utils.get_storage_capacity(run_name)
    hourly_results = utils.get_hourly_results(run_name)
    hourly_demand = utils.merge_dataframes_on_column(hourly_results, "demand_MWh")
    technologies = utils.read_yaml(f"../output/{run_name}/config.yaml")["technologies"]

    # Return the LCOE
    return lcoe.calculate(production_capacity, storage_capacity, hourly_demand, technologies=technologies)


def unconstrained_lcoe(run_name):
    """
    Calculate the unconstrained_lcoe LCOE for a specific run
    """
    assert validate.is_string(run_name)

    # Get the capacities and demand
    production_capacity = utils.get_production_capacity(run_name)
    storage_capacity = utils.get_storage_capacity(run_name)
    hourly_results = utils.get_hourly_results(run_name)
    hourly_demand = utils.merge_dataframes_on_column(hourly_results, "production_total_MWh")
    technologies = utils.read_yaml(f"../output/{run_name}/config.yaml")["technologies"]

    # Return the LCOE
    return lcoe.calculate(production_capacity, storage_capacity, hourly_demand, technologies=technologies)


def premium(run_name):
    """
    Calculate the firm kWh premium
    """
    assert validate.is_string(run_name)

    # Get the capacities and demand
    firm_lcoe = firm_lcoe(run_name)
    unconstrained_lcoe = firm_lcoe(unconstrained_lcoe)

    # Return the firm kWh premium
    return firm_lcoe / unconstrained_lcoe


def relative_curtailment(run_name):
    """
    Calculate the relative curtailment
    """
    assert validate.is_string(run_name)

    hourly_results = utils.get_hourly_results(run_name, group="all")
    return hourly_results.curtailed_MWh.sum() / hourly_results.production_total_MWh.sum()


def production_capacity(run_name):
    """
    Return a dictionary with the production capacity per production type
    """
    assert validate.is_string(run_name)

    production_capacity = utils.get_production_capacity(run_name, group="all")
    return production_capacity.to_dict()


def storage_capacity(run_name, *, type):
    """
    Return a dictionary with the storage capacity per storage type for either 'energy' or 'power'
    """
    assert validate.is_string(run_name)
    assert validate.is_string(type)

    storage_capacity = utils.get_storage_capacity(run_name, group="all")
    storage_capacity = storage_capacity[storage_capacity.index.get_level_values(1) == type]
    storage_capacity = storage_capacity.droplevel(1)
    return storage_capacity.to_dict()
