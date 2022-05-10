import streamlit as st

import utils
import validate


# @st.experimental_memo
def get_production_capacity(run_name, *, group=None, countries=None):
    """
    Return the (grouped) production capacity
    """
    assert validate.is_string(run_name)
    assert validate.is_aggregation_level(group, required=False)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # Get the production data
    production_capacity = utils.read_csv(f"../output/{run_name}/capacities/production.csv", index_col=0)
    if countries:
        bidding_zones = utils.get_bidding_zones_for_countries(countries)
        production_capacity = production_capacity[production_capacity.index.isin(bidding_zones)]

    # Return all bidding zones individually if not grouped
    if group is None:
        return production_capacity

    # Return the sum of all bidding zones per country
    if group == "country":
        production_capacity["country"] = production_capacity.index.to_series().apply(utils.get_country_of_bidding_zone)
        grouped_production_capacity = production_capacity.groupby(["country"]).sum()
        return grouped_production_capacity

    # Return the sum of all bidding zones
    if group == "all":
        return production_capacity.sum()
