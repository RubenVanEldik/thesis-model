import streamlit as st
import utils
import validate


def get_production_potential_in_climate_zone(bidding_zone, production_technology, *, config):
    """
    Calculate the production capacity per climate zone for a specific bidding zone and production technology
    """
    assert validate.is_bidding_zone(bidding_zone)
    assert validate.is_technology(production_technology)
    assert validate.is_config(config)

    # Get the country for this bidding zone
    country_code = utils.get_country_of_bidding_zone(bidding_zone)
    country = next(country for country in config["countries"] if country["nuts_2"] == country_code)

    # Return infinite if the production technology has no potential specified for this country
    if not production_technology in country["potential"]:
        return float("inf")

    # Calculate the number of climate zones in the country
    climate_zone_count = 0
    for bidding_zone_in_country in country["bidding_zones"]:
        temporal_data = utils.read_temporal_data(f"./input/bidding_zones/{config['model_year']}/{bidding_zone_in_country}.csv")
        climate_zone_count += len([column for column in temporal_data.columns if column.startswith(f"{production_technology}_")])

    # Return the production potential in the country divided by the number of climate zones in the country
    return country["potential"][production_technology] / climate_zone_count
