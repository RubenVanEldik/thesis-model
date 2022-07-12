import streamlit as st

import utils
import validate


@st.experimental_memo(show_spinner=False)
def get_country_of_bidding_zone(bidding_zone):
    """
    Find to which country a bidding zone belongs to
    """
    assert validate.is_bidding_zone(bidding_zone)

    countries = utils.read_yaml(utils.path("input", "countries.yaml"))
    return next(country["nuts_2"] for country in countries if bidding_zone in country["bidding_zones"])
