import pandas as pd
import streamlit as st

import utils
import technologies


def _calculate_annualized_production_costs(production_technologies, production_capacity_MW):
    """
    Calculate the annualized production costs
    """
    # Calculate the total annual production costs
    annualized_costs_production = 0
    for technology, assumptions in production_technologies.items():
        capacity_kW = production_capacity_MW[technology] * 1000
        capex = capacity_kW * assumptions["capex"]
        fixed_om = capacity_kW * assumptions["fixed_om"]
        crf = assumptions["crf"]
        annualized_costs_production += crf * capex + fixed_om

    return annualized_costs_production


def _calculate_annualized_storage_costs(storage_technologies, storage_capacity_MWh):
    """
    Calculate the annualized storage costs
    """
    # Calculate the total annual storage costs
    annualized_costs_storage = 0
    for technology, assumptions in storage_technologies.items():
        capacity_energy_kWh = storage_capacity_MWh[(technology, "energy")] * 1000
        capacity_power_kW = storage_capacity_MWh[(technology, "power")] * 1000

        capex_energy = capacity_energy_kWh * assumptions["energy_capex"]
        capex_power = capacity_power_kW * assumptions["power_capex"]
        capex = capex_energy + capex_power
        fixed_om = capex * assumptions["fixed_om"]
        crf = assumptions["crf"]
        annualized_costs_storage += crf * capex + fixed_om

    return annualized_costs_storage


def _calculate_annual_demand(demand_MWh):
    """
    Calculate the annual electricity demand
    """
    demand_start_date = demand_MWh.index.min()
    demand_end_date = demand_MWh.index.max()
    share_of_year_modelled = (demand_end_date - demand_start_date) / pd.Timedelta(365, "days")
    return demand_MWh.sum() / share_of_year_modelled


def calculate(production_capacity_per_bidding_zone, storage_capacity_per_bidding_zone, demand_per_bidding_zone, *, technologies, unconstrained=False):
    """
    Calculate the average LCOE for all bidding zones
    """
    annualized_production_costs = 0
    annualized_storage_costs = 0
    annual_electricity_demand = 0
    demand_column = "production_total_MWh" if unconstrained else "demand_MWh"

    for bidding_zone in production_capacity_per_bidding_zone.index:
        annualized_production_costs += _calculate_annualized_production_costs(technologies["production"], production_capacity_per_bidding_zone.loc[bidding_zone])
        annualized_storage_costs += _calculate_annualized_storage_costs(technologies["storage"], storage_capacity_per_bidding_zone.loc[bidding_zone])
        annual_electricity_demand += _calculate_annual_demand(demand_per_bidding_zone[bidding_zone][demand_column])

    # Calculate and return the LCOE
    lcoe_dollar = (annualized_production_costs + annualized_storage_costs) / annual_electricity_demand
    eur_usd = 1.1290  # Source: https://www.federalreserve.gov/releases/h10/20220110/
    return lcoe_dollar / eur_usd
