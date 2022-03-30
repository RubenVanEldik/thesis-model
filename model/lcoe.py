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


def _pv(parameter, *, year):
    """
    Calculate the average value of a specific parameter for PV
    """
    assumptions = technologies.assumptions("generation", "pv")

    # Calculate the average
    average_value = 0
    for pv_scale, share in assumptions["scales"].items():
        value = technologies.get_pv_param(pv_scale, parameter=parameter, year=year)
        average_value += float(share) * value

    # Return the average value
    return average_value


def _wind(type, parameter, *, year):
    """
    Calculate the average value for a specific parameter for onshore or offshore wind
    """
    assumptions = technologies.assumptions("generation", type)

    # Set the correct NREL technology name
    if type == "onshore":
        technology = "LandbasedWind"
    elif type == "offshore":
        technology = "OffShoreWind"
    else:
        raise ValueError("Invalid wind resource type")

    # Calculate the average
    average_value = 0
    for resource_class, share in assumptions["classes"].items():
        value = technologies.get_wind_param(
            technology, parameter=parameter, year=year, resource_class=resource_class
        )
        average_value += float(share) * value

    # Return the average value
    return average_value


def calculate(generation_capacity_MW, demand_MWh, year):
    """
    Calculate the levelized cost of energy using a given capacity and demand
    """
    # Unpack capacity variables
    capacity_pv_kWh = generation_capacity_MW["pv"] * 1000
    capacity_onshore_kWh = generation_capacity_MW["onshore"] * 1000
    capacity_offshore_kWh = generation_capacity_MW["offshore"] * 1000

    # Calculate CAPEX
    parameter = "CAPEX"
    capex_pv = capacity_pv_kWh * _pv(parameter, year=year)
    capex_onshore = capacity_onshore_kWh * _wind("onshore", parameter, year=year)
    capex_offshore = capacity_offshore_kWh * _wind("offshore", parameter, year=year)

    # Calculate annual fixed O&M
    parameter = "Fixed O&M"
    fixed_om_pv = capacity_pv_kWh * _pv(parameter, year=year)
    fixed_om_onshore = capacity_onshore_kWh * _wind("onshore", parameter, year=year)
    fixed_om_offshore = capacity_offshore_kWh * _wind("offshore", parameter, year=year)

    # Calculate annual variable O&M
    # TODO: The current variable calculation is wrong, but because its 0 it does not matter yet
    parameter = "Variable O&M"
    variable_om_pv = capacity_pv_kWh * _pv(parameter, year=year)
    variable_om_onshore = capacity_onshore_kWh * _wind("onshore", parameter, year=year)
    variable_om_offshore = capacity_offshore_kWh * _wind("offshore", parameter, year=year)

    # Calculate WACC
    parameter = "WACC Nominal"
    wacc_pv = _pv(parameter, year=year)
    wacc_onshore = _wind("onshore", parameter, year=year)
    wacc_offshore = _wind("offshore", parameter, year=year)

    # Get the lifetime of the technologies
    assumptions = utils.open_yaml("../input/technologies/assumptions.yaml")
    lifetime_pv = int(assumptions["pv"]["lifetime"])
    lifetime_onshore = int(assumptions["onshore"]["lifetime"])
    lifetime_offshore = int(assumptions["offshore"]["lifetime"])

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
