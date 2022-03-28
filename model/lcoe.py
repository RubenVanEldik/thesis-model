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


def _pv(capacity_MW, *, year, parameter):
    """
    Calculate the average value of a specific parameter for PV
    """
    assumptions = technologies.assumptions("pv")

    # Calculate the average
    average_value = 0
    for pv_scale in assumptions["scales"]:
        share = float(assumptions["scales"][pv_scale])
        value = technologies.get_pv_param(pv_scale, parameter=parameter, year=year)
        average_value += share * value

    # Return the average value
    return average_value


def _wind(type, capacity_MW, *, year, parameter):
    """
    Calculate the average value for a specific parameter for onshore or offshore wind
    """
    assumptions = technologies.assumptions(type)

    # Set the correct NREL technology name
    if type == "onshore":
        technology = "LandbasedWind"
    elif type == "offshore":
        technology = "OffShoreWind"
    else:
        raise ValueError("Invalid wind resource type")

    # Calculate the average
    average_value = 0
    for resource_class in assumptions["classes"]:
        share = float(assumptions["classes"][resource_class])
        value = technologies.get_wind_param(
            technology, parameter=parameter, year=year, resource_class=resource_class
        )
        average_value += share * value

    # Return the average value
    return average_value


def calculate(generation_capacity, demand, year):
    """
    Calculate the levelized cost of energy using a given capacity and demand
    """
    # Unpack capacity variables
    capacity_pv = generation_capacity["pv"]
    capacity_onshore = generation_capacity["onshore"]
    capacity_offshore = generation_capacity["offshore"]

    # Calculate CAPEX
    parameter = "CAPEX"
    capex_pv = _pv(capacity_pv, year=year, parameter=parameter)
    capex_onshore = _wind("onshore", capacity_onshore, year=year, parameter=parameter)
    capex_offshore = _wind("offshore", capacity_offshore, year=year, parameter=parameter)

    # Calculate annual fixed O&M
    parameter = "Fixed O&M"
    fixed_om_pv = _pv(capacity_pv, year=year, parameter=parameter)
    fixed_om_onshore = _wind("onshore", capacity_onshore, year=year, parameter=parameter)
    fixed_om_offshore = _wind("offshore", capacity_offshore, year=year, parameter=parameter)

    # # Calculate annual variable O&M
    parameter = "Variable O&M"
    variable_om_pv = _pv(capacity_pv, year=year, parameter=parameter)
    variable_om_onshore = _wind("onshore", capacity_onshore, year=year, parameter=parameter)
    variable_om_offshore = _wind("offshore", capacity_offshore, year=year, parameter=parameter)

    # Calculate WACC
    parameter = "WACC Nominal"
    wacc_pv = _pv(1, year=year, parameter=parameter)
    wacc_onshore = _wind("onshore", 1, year=year, parameter=parameter)
    wacc_offshore = _wind("offshore", 1, year=year, parameter=parameter)

    # Get the lifetime of the technologies
    assumptions = utils.open_yaml("../input/technologies/assumptions.yaml")
    lifetime_pv = int(assumptions["pv"]["lifetime"])
    lifetime_onshore = int(assumptions["onshore"]["lifetime"])
    lifetime_offshore = int(assumptions["offshore"]["lifetime"])

    # Calculate total fixed O&M
    lifetime_om_pv = _calculate_lifetime_costs(fixed_om_pv + variable_om_pv, wacc_pv, lifetime_pv)
    lifetime_om_onshore = _calculate_lifetime_costs(
        fixed_om_onshore + variable_om_onshore, wacc_onshore, lifetime_onshore
    )
    lifetime_om_offshore = _calculate_lifetime_costs(
        fixed_om_offshore + variable_om_offshore, wacc_offshore, lifetime_offshore
    )

    # Calculate the total of all parts
    total_capex = capex_pv + capex_onshore + capex_offshore
    total_om = lifetime_om_pv + lifetime_om_onshore + lifetime_om_offshore
    total_electricity_consumption = demand.sum()

    # Calculate and return the CAPEX
    capex = (total_capex + total_om) / total_electricity_consumption
    return capex
