import streamlit as st

import lcoe
import validate
import utils


@st.experimental_memo
def _get_production_capacity(timestamp, *, group=None):
    """
    Return the (grouped) production capacity
    """
    assert validate.is_timestamp_string(timestamp)
    assert validate.is_aggregation_level(group, required=False)

    # Get the production data
    production_capacity = utils.open_yaml(f"../output/{timestamp}/production.yaml")

    # Return all bidding zones individually if not grouped
    if group is None:
        return production_capacity

    # Return the sum of all bidding zones per country
    if group == "country":
        production_capacity_per_country = {}
        for bidding_zone, production_capacity_local in production_capacity.items():
            country_code = utils.get_country_of_bidding_zone(bidding_zone)
            if not production_capacity_per_country.get(country_code):
                production_capacity_per_country[country_code] = {}
            for technology in production_capacity_local:
                production_capacity_per_country[country_code][technology] = production_capacity_per_country[country_code].get(technology, 0) + production_capacity_local[technology]
        return production_capacity_per_country

    # Return the sum of all bidding zones
    if group == "all":
        total_production_capacity = {}
        for production_capacity_local in production_capacity.values():
            for technology in production_capacity_local:
                total_production_capacity[technology] = total_production_capacity.get(technology, 0) + production_capacity_local[technology]
        return total_production_capacity


@st.experimental_memo
def _get_storage_capacity(timestamp, *, group=None):
    """
    Return the (grouped) storage capacity
    """
    assert validate.is_timestamp_string(timestamp)
    assert validate.is_aggregation_level(group, required=False)

    # Get the storage data
    storage_capacity = utils.open_yaml(f"../output/{timestamp}/storage.yaml")

    # Return all bidding zones individually if not grouped
    if group is None:
        return storage_capacity

    # Return the sum of all bidding zones per country
    if group == "country":
        storage_capacity_per_country = {}
        for bidding_zone, storage_capacity_local in storage_capacity.items():
            country_code = utils.get_country_of_bidding_zone(bidding_zone)
            if not storage_capacity_per_country.get(country_code):
                storage_capacity_per_country[country_code] = {}
            for technology in storage_capacity_local:
                if not storage_capacity_per_country[country_code].get(technology):
                    storage_capacity_per_country[country_code][technology] = {"energy": 0, "power": 0}
                storage_capacity_per_country[country_code][technology]["energy"] += storage_capacity_local[technology]["energy"]
                storage_capacity_per_country[country_code][technology]["power"] += storage_capacity_local[technology]["power"]
        return storage_capacity_per_country

    # Return the sum of all bidding zones
    if group == "all":
        total_storage_capacity = {}
        for storage_capacity_local in storage_capacity.values():
            for technology in storage_capacity_local:
                if not total_storage_capacity.get(technology):
                    total_storage_capacity[technology] = {"energy": 0, "power": 0}
                total_storage_capacity[technology]["energy"] += storage_capacity_local[technology]["energy"]
                total_storage_capacity[technology]["power"] += storage_capacity_local[technology]["power"]
        return total_storage_capacity


@st.experimental_memo
def _get_hourly_results(timestamp, *, group=None):
    """
    Return the (grouped) production capacity
    """
    assert validate.is_timestamp_string(timestamp)
    assert validate.is_aggregation_level(group, required=False)

    # Get the config
    config = utils.open_yaml(f"../output/{timestamp}/config.yaml")

    # Get the hourly data for each bidding zone
    hourly_results = {}
    for country in config["countries"]:
        for bidding_zone in country["zones"]:
            filepath = f"../output/{timestamp}/bidding_zones/{bidding_zone}.csv"
            hourly_results[bidding_zone] = utils.read_hourly_data(filepath)

            if hourly_results[bidding_zone].isnull().values.any():
                st.warning(f"Bidding zone {bidding_zone} contains NaN values")

    # Return all bidding zones individually if not grouped
    if group is None:
        return hourly_results

    # Return the sum of all bidding zones per country
    if group == "country":
        hourly_results_per_country = {}
        for bidding_zone, hourly_results_local in hourly_results.items():
            country_code = utils.get_country_of_bidding_zone(bidding_zone)
            if hourly_results_per_country.get(country_code) is None:
                hourly_results_per_country[country_code] = hourly_results_local
            else:
                hourly_results_per_country[country_code] += hourly_results_local
        return hourly_results_per_country

    # Return the sum of all bidding zones
    if group == "all":
        total_hourly_results = None
        for hourly_results_local in hourly_results.values():
            if total_hourly_results is None:
                total_hourly_results = hourly_results_local.copy(deep=True)
            else:
                total_hourly_results += hourly_results_local
        return total_hourly_results


def hourly_results(timestamp):
    """
    Show the hourly results in a chart and table
    """
    assert validate.is_timestamp_string(timestamp)

    # Get hourly results for a country
    all_hourly_results = _get_hourly_results(timestamp, group="country")
    config = utils.open_yaml(f"../output/{timestamp}/config.yaml")
    country = st.selectbox("Country", config["countries"], format_func=lambda country: country["name"])
    hourly_results = all_hourly_results[country["code"]]

    # Filter the data columns
    columns = st.multiselect("Columns", hourly_results.columns)
    hourly_results = hourly_results[columns] if columns else hourly_results

    # Filter the data temporarily
    start_data = hourly_results.index.min().to_pydatetime()
    end_data = hourly_results.index.max().to_pydatetime()
    data_range = st.slider("Date range", value=(start_data, end_data), min_value=start_data, max_value=end_data)
    hourly_results = hourly_results.loc[data_range[0] : data_range[1]]

    # Show the line chart
    st.line_chart(hourly_results)

    # Show the table in an expander
    with st.expander("Raw data"):
        st.write(hourly_results)


def statistics(timestamp):
    """
    Show the key indicators for a run
    """
    assert validate.is_timestamp_string(timestamp)

    # Get both the grouped and ungrouped results
    hourly_results = _get_hourly_results(timestamp)
    total_hourly_results = _get_hourly_results(timestamp, group="all")
    production_capacity = _get_production_capacity(timestamp)
    total_production_capacity = _get_production_capacity(timestamp, group="all")
    storage_capacity = _get_storage_capacity(timestamp)
    total_storage_capacity = _get_storage_capacity(timestamp, group="all")

    # Calculte the values
    firm_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results)
    unconstrained_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results, unconstrained=True)
    firm_kwh_premium = firm_lcoe / unconstrained_lcoe
    relative_curtailment = total_hourly_results.curtailed_MWh.sum() / total_hourly_results.total_production_MWh.sum()
    installed_pv = total_production_capacity["pv"]
    installed_onshore = total_production_capacity["onshore"]
    installed_offshore = total_production_capacity["offshore"]
    installed_lion_hours = total_storage_capacity["lion"]["energy"] / total_hourly_results.demand_MWh.mean()

    # Show the KPI's
    st.header("KPI's")
    col1, col2, col3 = st.columns(3)
    col1.metric("LCOE", f"{int(firm_lcoe)}€/MWh")
    col2.metric("Firm kWh premium", f"{firm_kwh_premium:.2f}")
    col3.metric("Curtailment", f"{relative_curtailment:.1%}")

    # Show the capacities
    st.header("Capacities")
    st.subheader("Production")
    col1, col2, col3 = st.columns(3)
    col1.metric("Solar PV", f"{int(installed_pv / 1000):,}GW")
    col2.metric("Onshore wind", f"{int(installed_onshore / 1000):,}GW")
    col3.metric("Offshore wind", f"{int(installed_offshore / 1000):,}GW")
    st.subheader("Storage")
    col1, col2, col3 = st.columns(3)
    col1.metric("Li-ion", f"{installed_lion_hours:.1f}Hr")
    col2.metric("Pumped hydro", "-")
    col3.metric("Hydrogen", "-")
