import pandas as pd
import streamlit as st

import utils
import technologies


def _calculate_production_costs(capacity, technology):
    """
    Calculate the total annual generation costs
    """
    assumptions = technologies.assumptions("production", technology)

    capacity_kWh = capacity[technology] * 1000
    capex = capacity_kWh * assumptions["capex"]
    fixed_om = capacity_kWh * assumptions["fixed_om"]
    crf = assumptions["crf"]
    return crf * capex + fixed_om


def _calculate_storage_costs(capacity, technology):
    """
    Calculate the total annual storage costs
    """
    assumptions = technologies.assumptions("storage", technology)

    capacity_energy_kWh = capacity[technology]["energy"] * 1000
    capacity_power_kW = capacity[technology]["power"] * 1000

    capex_energy = capacity_energy_kWh * assumptions["energy_capex"]
    capex_power = capacity_power_kW * assumptions["power_capex"]
    capex = capex_energy + capex_power
    fixed_om = capex * assumptions["fixed_om"]
    crf = assumptions["crf"]
    return crf * capex + fixed_om


def _calculate_annual_demand(demand_MWh):
    """
    Calculate the annual electricity demand
    """
    demand_start_date = demand_MWh.index.min()
    demand_end_date = demand_MWh.index.max()
    share_of_year_modelled = (demand_end_date - demand_start_date) / pd.Timedelta(365, "days")
    return demand_MWh.sum() / share_of_year_modelled


def calculate(generation_capacity_MW, storage_capacity_MWh, demand_MWh):
    """
    Calculate the levelized cost of energy using a given capacity and demand
    """
    # Calculate the total annual generation costs
    annualized_costs_generation = 0
    for technology in technologies.technology_types("production"):
        annualized_costs_generation += _calculate_production_costs(generation_capacity_MW, technology)

    # Calculate the total annual storage costs
    annualized_costs_storage = 0
    for technology in technologies.technology_types("storage"):
        annualized_costs_storage += _calculate_storage_costs(storage_capacity_MWh, technology)

    # Calculate the annual electricity demand
    annual_electricity_demand = _calculate_annual_demand(demand_MWh)

    # Calculate and return the LCOE
    lcoe_dollar = (annualized_costs_generation + annualized_costs_storage) / annual_electricity_demand
    eur_usd = 1.1290  # Source: https://www.federalreserve.gov/releases/h10/20220110/
    return lcoe_dollar / eur_usd
