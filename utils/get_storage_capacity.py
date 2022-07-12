import pandas as pd
import streamlit as st

import utils
import validate


@st.experimental_memo
def get_storage_capacity(run_name, resolution, *, group=None, countries=None):
    """
    Return the (grouped) storage capacity
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)
    assert validate.is_aggregation_level(group, required=False)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # If no countries are specified, set them to all countries modelled in this run
    if not countries:
        config = utils.read_yaml(utils.path("output", run_name, "config.yaml"))
        countries = [country["nuts_2"] for country in config["countries"]]

    # Get the storage capacity for each bidding zone
    storage_capacity = {}
    for bidding_zone in utils.get_bidding_zones_for_countries(countries):
        filepath = utils.path("output", run_name, resolution, "storage_capacities", f"{bidding_zone}.csv")
        storage_capacity[bidding_zone] = utils.read_csv(filepath, index_col=0)

    # Return a dictionary with the storage capacity per bidding zone DataFrame if not grouped
    if group is None:
        return storage_capacity

    # Return a dictionary with the storage capacity per country DataFrame
    if group == "country":
        storage_capacity_per_country = {}
        for bidding_zone, storage_capacity_local in storage_capacity.items():
            country_code = utils.get_country_of_bidding_zone(bidding_zone)
            if country_code not in storage_capacity_per_country:
                storage_capacity_per_country[country_code] = storage_capacity_local.copy(deep=True)
            else:
                storage_capacity_per_country[country_code] += storage_capacity_local
        return storage_capacity_per_country

    # Return a DataFrame with the total storage capacity per technology
    if group == "all":
        total_storage_capacity = None
        for bidding_zone, storage_capacity_local in storage_capacity.items():
            if total_storage_capacity is None:
                total_storage_capacity = storage_capacity_local.copy(deep=True)
            else:
                total_storage_capacity += storage_capacity_local
        return total_storage_capacity
