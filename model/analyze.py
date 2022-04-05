import pandas as pd
import streamlit as st
import datetime

import lcoe
import utils


def run(timestamp):
    output_folder = f"../output/{timestamp}"
    production_capacity = utils.open_yaml(f"{output_folder}/production.yaml")
    storage_capacity = utils.open_yaml(f"{output_folder}/storage.yaml")
    config = utils.open_yaml(f"{output_folder}/config.yaml")

    hourly_results = {}

    for country in config["countries"]:
        for bidding_zone in country["zones"]:
            filepath = f"{output_folder}/bidding_zones/{bidding_zone}.csv"
            hourly_results[bidding_zone] = utils.read_hourly_data(filepath)

    firm_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results)
    st.write(firm_lcoe)
