import streamlit as st

import lcoe
import utils


def run(timestamp):
    """
    Step 1: Import the results
    """
    output_folder = f"../output/{timestamp}"
    production_capacity = utils.open_yaml(f"{output_folder}/production.yaml")
    storage_capacity = utils.open_yaml(f"{output_folder}/storage.yaml")
    config = utils.open_yaml(f"{output_folder}/config.yaml")

    hourly_results = {}
    for country in config["countries"]:
        for bidding_zone in country["zones"]:
            filepath = f"{output_folder}/bidding_zones/{bidding_zone}.csv"
            hourly_results[bidding_zone] = utils.read_hourly_data(filepath)

            if hourly_results[bidding_zone].isnull().values.any():
                st.warning(f"Bidding zone {bidding_zone} contains NaN values")

    """
    Step 2: Group all results
    """
    # Group the production capacity
    total_production_capacity = {}
    for production_capacity_local in production_capacity.values():
        for technology in production_capacity_local:
            total_production_capacity[technology] = total_production_capacity.get(technology, 0) + production_capacity_local[technology]

    # Group the storage capacity
    total_storage_capacity = {}
    for storage_capacity_local in storage_capacity.values():
        for technology in storage_capacity_local:
            if not total_storage_capacity.get(technology):
                total_storage_capacity[technology] = {"energy": 0, "power": 0}
            total_storage_capacity[technology]["energy"] += storage_capacity_local[technology]["energy"]
            total_storage_capacity[technology]["power"] += storage_capacity_local[technology]["power"]

    # Group the hourly results
    total_hourly_results = None
    for hourly_results_local in hourly_results.values():
        if total_hourly_results is None:
            total_hourly_results = hourly_results_local.copy(deep=True)
        else:
            total_hourly_results += hourly_results_local

    """
    Step 3: Show the hourly data for a specific bidding zone
    """
    # Show a line chart with the hourly data
    with st.expander("Hourly data"):
        bidding_zone = st.selectbox("Bidding zone", hourly_results.keys())
        columns = st.multiselect("Columns", hourly_results[bidding_zone].columns)
        st.line_chart(hourly_results[bidding_zone][columns] if columns else hourly_results[bidding_zone])
        st.write(hourly_results[bidding_zone])

    """
    Step 2: Calculate and show the main indicators
    """
    firm_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results)
    unconstrained_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results, unconstrained=True)
    firm_kwh_premium = firm_lcoe / unconstrained_lcoe
    relative_curtailment = total_hourly_results.curtailed_MWh.sum() / total_hourly_results.total_production_MWh.sum()
    installed_pv = total_production_capacity["pv"]
    installed_onshore = total_production_capacity["onshore"]
    installed_offshore = total_production_capacity["offshore"]
    installed_lion = total_storage_capacity["lion"]["energy"]

    st.subheader("KPI's")
    col1, col2, col3 = st.columns(3)
    col1.metric("LCOE", f"{int(firm_lcoe)}€/MWh")
    col2.metric("Firm kWh premium", f"{firm_kwh_premium:.3}")
    col3.metric("Curtailment", f"{relative_curtailment:.1%}")

    st.subheader("Capacities")
    col1, col2, col3 = st.columns(3)
    col1.metric("Solar PV", f"{int(installed_pv / 1000):,}GW")
    col2.metric("Onshore wind", f"{int(installed_onshore / 1000):,}GW")
    col3.metric("Offshore wind", f"{int(installed_offshore / 1000):,}GW")
    col1.metric("Li-ion", f"{int(installed_lion / 1000):,}GWh")
    col2.metric("Pumped hydro", "-")
    col3.metric("Hydrogen", "-")
