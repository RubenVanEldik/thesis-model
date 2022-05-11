import streamlit as st

import utils
import validate


@st.experimental_memo
def get_storage_capacity(run_name, *, group=None, countries=None):
    """
    Return the (grouped) storage capacity
    """
    assert validate.is_string(run_name)
    assert validate.is_aggregation_level(group, required=False)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # Get the storage data
    storage_capacity = utils.read_csv(f"./output/{run_name}/capacities/storage.csv", index_col=0, header=[0, 1])
    if countries:
        bidding_zones = utils.get_bidding_zones_for_countries(countries)
        storage_capacity = storage_capacity[storage_capacity.index.isin(bidding_zones)]

    # Return all bidding zones individually if not grouped
    if group is None:
        return storage_capacity

    # Return the sum of all bidding zones per country
    if group == "country":
        storage_capacity["country"] = storage_capacity.index.to_series().apply(utils.get_country_of_bidding_zone)
        grouped_storage_capacity = storage_capacity.groupby(["country"]).sum()
        return grouped_storage_capacity

    # Return the sum of all bidding zones
    if group == "all":
        return storage_capacity.sum()
