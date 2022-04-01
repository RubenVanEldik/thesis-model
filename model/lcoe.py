import pandas as pd
import streamlit as st
import utils
import technologies


def calculate(generation_capacity_MW, storage_capacity_MWh, demand_MWh, year):
    """
    Calculate the levelized cost of energy using a given capacity and demand
    """
    # Unpack generation capacity variables
    capacity_pv_kWh = generation_capacity_MW["pv"] * 1000
    capacity_onshore_kWh = generation_capacity_MW["onshore"] * 1000
    capacity_offshore_kWh = generation_capacity_MW["offshore"] * 1000

    # Unpack storage capacity variables
    capacity_lion_energy_kWh = storage_capacity_MWh["lion"]["energy"] * 1000
    capacity_lion_power_kW = storage_capacity_MWh["lion"]["power"] * 1000

    # Get all assumptions
    assumptions_pv = technologies.assumptions("production", "pv")
    assumptions_onshore = technologies.assumptions("production", "onshore")
    assumptions_offshore = technologies.assumptions("production", "offshore")
    assumptions_lion = technologies.assumptions("storage", "lion")

    # Calculate CAPEX
    capex_pv = capacity_pv_kWh * assumptions_pv["capex"]
    capex_onshore = capacity_onshore_kWh * assumptions_onshore["capex"]
    capex_offshore = capacity_offshore_kWh * assumptions_offshore["capex"]
    capex_lion_energy = capacity_lion_energy_kWh * assumptions_lion["energy_capex"]
    capex_lion_power = capacity_lion_power_kW * assumptions_lion["power_capex"]
    capex_lion = capex_lion_energy + capex_lion_power

    # Calculate annual fixed O&M
    fixed_om_pv = capacity_pv_kWh * assumptions_pv["fixed_om"]
    fixed_om_onshore = capacity_onshore_kWh * assumptions_onshore["fixed_om"]
    fixed_om_offshore = capacity_offshore_kWh * assumptions_offshore["fixed_om"]
    fixed_om_lion = capex_lion * assumptions_lion["fixed_om"]

    # None of the generation and storage technologies have variable O&M costs

    # Unpack capital recovery factors
    crf_pv = assumptions_pv["crf"]
    crf_onshore = assumptions_onshore["crf"]
    crf_offshore = assumptions_offshore["crf"]
    crf_lion = assumptions_lion["crf"]

    # Calculate the annual electricity demand
    demand_start_date = demand_MWh.index.min()
    demand_end_date = demand_MWh.index.max()
    share_of_lifetime_modeled = (demand_end_date - demand_start_date) / pd.Timedelta(365, "days")
    annual_electricity_consumption = demand_MWh.sum() / share_of_lifetime_modeled

    # Calculate the total annualized costs
    annual_costs_pv = crf_pv * capex_pv + fixed_om_pv
    annual_costs_onshore = crf_onshore * capex_onshore + fixed_om_onshore
    annual_costs_offshore = crf_offshore * capex_offshore + fixed_om_offshore
    annual_costs_lion = crf_lion * capex_lion + fixed_om_lion
    annual_costs_generation = annual_costs_pv + annual_costs_onshore + annual_costs_offshore
    annual_costs_storage = annual_costs_lion

    # Calculate and return the LCOE
    lcoe_dollar = (annual_costs_generation + annual_costs_storage) / annual_electricity_consumption
    eur_usd = 1.1290  # Source: https://www.federalreserve.gov/releases/h10/20220110/
    return lcoe_dollar / eur_usd
