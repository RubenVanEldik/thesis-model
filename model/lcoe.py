import pandas as pd
import streamlit as st
import utils
import technologies


def _calculate_lifetime_costs(annual_costs, wacc, lifetime):
    """
    Calculate the total lifetime costs of an annual cost
    """
    lifetime_costs = 0
    for year in range(1, lifetime + 1):
        lifetime_costs += annual_costs / (1 + wacc) ** year
    return lifetime_costs


def calculate(generation_capacity_MW, demand_MWh, year):
    """
    Calculate the levelized cost of energy using a given capacity and demand
    """
    # Unpack capacity variables
    capacity_pv_kWh = generation_capacity_MW["pv"] * 1000
    capacity_onshore_kWh = generation_capacity_MW["onshore"] * 1000
    capacity_offshore_kWh = generation_capacity_MW["offshore"] * 1000

    # Get all assumptions
    assumptions_pv = technologies.assumptions("production", "pv")
    assumptions_onshore = technologies.assumptions("production", "onshore")
    assumptions_offshore = technologies.assumptions("production", "offshore")

    # Calculate CAPEX
    capex_pv = capacity_pv_kWh * assumptions_pv["capex"]
    capex_onshore = capacity_onshore_kWh * assumptions_onshore["capex"]
    capex_offshore = capacity_offshore_kWh * assumptions_offshore["capex"]

    # Calculate annual fixed O&M
    fixed_om_pv = capacity_pv_kWh * assumptions_pv["fixed_om"]
    fixed_om_onshore = capacity_onshore_kWh * assumptions_onshore["fixed_om"]
    fixed_om_offshore = capacity_offshore_kWh * assumptions_offshore["fixed_om"]

    # Calculate annual variable O&M
    # TODO: The current variable calculation is wrong, but because its 0 it does not matter yet
    variable_om_pv = capacity_pv_kWh * assumptions_pv["variable_om"]
    variable_om_onshore = capacity_onshore_kWh * assumptions_onshore["variable_om"]
    variable_om_offshore = capacity_offshore_kWh * assumptions_offshore["variable_om"]

    # Calculate WACC
    wacc_pv = assumptions_pv["wacc"]
    wacc_onshore = assumptions_onshore["wacc"]
    wacc_offshore = assumptions_offshore["wacc"]

    # Get the lifetime of the technologies
    lifetime_pv = assumptions_pv["economic_lifetime"]
    lifetime_onshore = assumptions_onshore["economic_lifetime"]
    lifetime_offshore = assumptions_offshore["economic_lifetime"]

    # Calculate total O&M
    lifetime_om_pv = _calculate_lifetime_costs(fixed_om_pv + variable_om_pv, wacc_pv, lifetime_pv)
    lifetime_om_onshore = _calculate_lifetime_costs(
        fixed_om_onshore + variable_om_onshore, wacc_onshore, lifetime_onshore
    )
    lifetime_om_offshore = _calculate_lifetime_costs(
        fixed_om_offshore + variable_om_offshore, wacc_offshore, lifetime_offshore
    )

    # Calculate the total CAPEX and O&M
    total_capex = capex_pv + capex_onshore + capex_offshore
    total_om = lifetime_om_pv + lifetime_om_onshore + lifetime_om_offshore

    # Calculate the total electricity demand over the lifetime
    demand_start_date = demand_MWh.index.min()
    demand_end_date = demand_MWh.index.max()
    # TODO: The current average_lifetime is more wrong than trickle-down economics
    average_lifetime = pd.Timedelta(20 * 365, "days")
    share_of_lifetime_modeled = (demand_end_date - demand_start_date) / average_lifetime
    total_electricity_consumption = demand_MWh.sum() / share_of_lifetime_modeled

    # Calculate and return the CAPEX
    capex_dollar = (total_capex + total_om) / total_electricity_consumption
    eur_usd = 1.1290  # Source: https://www.federalreserve.gov/releases/h10/20220110/
    return capex_dollar / eur_usd
