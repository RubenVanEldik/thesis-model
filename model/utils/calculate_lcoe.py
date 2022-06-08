import pandas as pd
import streamlit as st

import utils
import validate


def _calculate_annualized_production_costs(production_technologies, production_capacity_MW):
    """
    Calculate the annualized production costs
    """
    assert validate.is_dict(production_technologies)
    assert validate.is_series(production_capacity_MW)

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
    assert validate.is_dict(storage_technologies)
    assert validate.is_series(storage_capacity_MWh)

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
    assert validate.is_series(demand_MWh)

    demand_start_date = demand_MWh.index.min()
    demand_end_date = demand_MWh.index.max()
    share_of_year_modelled = (demand_end_date - demand_start_date) / pd.Timedelta(365, "days")
    return demand_MWh.sum() / share_of_year_modelled


def calculate_lcoe(production_capacity_per_bidding_zone, storage_capacity_per_bidding_zone, demand_per_bidding_zone, *, config):
    """
    Calculate the average LCOE for all bidding zones
    """
    assert validate.is_dataframe(production_capacity_per_bidding_zone, column_validator=validate.is_technology)
    assert validate.is_dataframe(storage_capacity_per_bidding_zone, required=False)
    assert validate.is_dataframe(demand_per_bidding_zone, column_validator=validate.is_bidding_zone)
    assert validate.is_config(config)

    annualized_production_costs = 0
    annualized_storage_costs = 0
    annual_electricity_demand = 0

    for bidding_zone in production_capacity_per_bidding_zone.index:
        # Add the annualized production costs
        annualized_production_costs += _calculate_annualized_production_costs(config["technologies"]["production"], production_capacity_per_bidding_zone.loc[bidding_zone])

        # Add the annualized storage costs if there is any storage
        if storage_capacity_per_bidding_zone is not None:
            annualized_storage_costs += _calculate_annualized_storage_costs(config["technologies"]["storage"], storage_capacity_per_bidding_zone.loc[bidding_zone])

        # Add the annual electricity demand
        annual_electricity_demand += _calculate_annual_demand(demand_per_bidding_zone[bidding_zone])

    # Calculate and return the LCOE
    lcoe_dollar = (annualized_production_costs + annualized_storage_costs) / annual_electricity_demand
    eur_usd = 1.1290  # Source: https://www.federalreserve.gov/releases/h10/20220110/
    return lcoe_dollar / eur_usd