import streamlit as st

import utils
import validate


@st.experimental_memo
def get_bidding_zones_for_countries(country_codes):
    """
    Return a flat list with all bidding zones for a given list of countries
    """
    assert validate.is_country_code_list(country_codes, type="nuts_2")

    # Get the countries
    countries = utils.read_yaml("./input/countries.yaml")

    # Add the bidding zones for each country to the bidding_zones list
    bidding_zones = []
    for country_code in country_codes:
        country = next(country for country in countries if country["nuts_2"] == country_code)
        bidding_zones += country["zones"]

    return bidding_zones
