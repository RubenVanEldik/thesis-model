import pandas as pd
import streamlit as st

import utils
import validate


# @st.experimental_memo
def get_production_capacity(run_name, resolution, *, group=None, countries=None):
    """
    Return the (grouped) production capacity
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)
    assert validate.is_aggregation_level(group, required=False)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # If no countries are specified, set them to all countries modelled in this run
    if not countries:
        config = utils.read_yaml(f"./output/{run_name}/config.yaml")
        countries = [country["nuts_2"] for country in config["countries"]]

    # Get the production capacity for each bidding zone
    production_capacity = {}
    for bidding_zone in utils.get_bidding_zones_for_countries(countries):
        filepath = f"./output/{run_name}/{resolution}/production_capacities/{bidding_zone}.csv"
        production_capacity[bidding_zone] = utils.read_csv(filepath, index_col=0)

    # Return a dictionary with the production capacity per bidding zone DataFrame if not grouped
    if group is None:
        return production_capacity

    # Return a DataFrame with the production capacity per country
    if group == "country":
        production_capacity_per_country = None
        for bidding_zone, production_capacity_local in production_capacity.items():
            country_code = utils.get_country_of_bidding_zone(bidding_zone)
            if production_capacity_per_country is None:
                production_capacity_per_country = pd.DataFrame(columns=production_capacity_local.columns)
            if country_code not in production_capacity_per_country.index:
                production_capacity_per_country.loc[country_code] = production_capacity_local.sum()
            else:
                production_capacity_per_country.loc[country_code] += production_capacity_local.sum()
        return production_capacity_per_country

    # Return a Series with the total production capacity per technology
    if group == "all":
        total_production_capacity = None
        for bidding_zone, production_capacity_local in production_capacity.items():
            if total_production_capacity is None:
                total_production_capacity = production_capacity_local.sum()
            else:
                total_production_capacity += production_capacity_local.sum()
        return total_production_capacity
