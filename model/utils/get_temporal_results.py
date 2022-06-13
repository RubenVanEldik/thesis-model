import streamlit as st

import utils
import validate


@st.experimental_memo
def get_temporal_results(run_name, *, group=None, countries=None):
    """
    Return the (grouped) production capacity
    """
    assert validate.is_string(run_name)
    assert validate.is_aggregation_level(group, required=False)
    assert validate.is_country_code_list(countries, type="nuts_2", required=False)

    # If no countries are specified, set them to all countries modelled in this run
    if not countries:
        config = utils.read_yaml(f"./output/{run_name}/config.yaml")
        countries = [country["nuts_2"] for country in config["countries"]]

    # Get the temporal data for each bidding zone
    temporal_results = {}
    bidding_zones = utils.get_bidding_zones_for_countries(countries)
    for bidding_zone in bidding_zones:
        filepath = f"./output/{run_name}/temporal_results/{bidding_zone}.csv"
        temporal_results[bidding_zone] = utils.read_temporal_data(filepath)

        if temporal_results[bidding_zone].isnull().values.any():
            st.warning(f"Bidding zone {bidding_zone} contains NaN values")

    # Return all bidding zones individually if not grouped
    if group is None:
        return temporal_results

    # Return the sum of all bidding zones per country
    if group == "country":
        temporal_results_per_country = {}
        for bidding_zone, temporal_results_local in temporal_results.items():
            country_code = utils.get_country_of_bidding_zone(bidding_zone)
            if temporal_results_per_country.get(country_code) is None:
                temporal_results_per_country[country_code] = temporal_results_local
            else:
                temporal_results_per_country[country_code] += temporal_results_local
        return temporal_results_per_country

    # Return the sum of all bidding zones
    if group == "all":
        total_temporal_results = None
        for temporal_results_local in temporal_results.values():
            if total_temporal_results is None:
                total_temporal_results = temporal_results_local.copy(deep=True)
            else:
                total_temporal_results += temporal_results_local
        return total_temporal_results
