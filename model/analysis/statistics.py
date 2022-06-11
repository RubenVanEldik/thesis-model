import streamlit as st

import stats
import utils
import validate


def statistics(run_name):
    """
    Show the key indicators for a run
    """
    assert validate.is_string(run_name)

    st.title("📊 Statistics")

    # Ask for which countries the statistics should be shown
    config = utils.read_yaml(f"./output/{run_name}/config.yaml")
    selected_countries = st.sidebar.multiselect("Countries", config["countries"], format_func=lambda country: country["name"])
    selected_country_codes = [country["nuts_2"] for country in selected_countries]

    # Show the KPI's
    with st.expander("KPI's", expanded=True):
        col1, col2, col3 = st.columns(3)

        # LCOE
        firm_lcoe_selected = stats.firm_lcoe(run_name, countries=selected_country_codes)
        firm_lcoe_all = stats.firm_lcoe(run_name)
        lcoe_delta = f"{(firm_lcoe_selected / firm_lcoe_all) - 1:.0%}" if selected_country_codes else None
        col1.metric("LCOE", f"{int(firm_lcoe_selected)}€/MWh", lcoe_delta, delta_color="inverse")

        # Firm kWh premium
        premium_selected = stats.premium(run_name, countries=selected_country_codes)
        premium_all = stats.premium(run_name)
        premium_delta = f"{(premium_selected / premium_all) - 1:.0%}" if selected_country_codes else None
        col2.metric("Firm kWh premium", f"{premium_selected:.2f}", premium_delta, delta_color="inverse")

        # Curtailment
        curtailment_selected = stats.relative_curtailment(run_name, countries=selected_country_codes)
        curtailment_all = stats.relative_curtailment(run_name)
        curtailment_delta = f"{(curtailment_selected / curtailment_all) - 1:.0%}" if selected_country_codes else None
        col3.metric("Curtailment", f"{curtailment_selected:.1%}", curtailment_delta, delta_color="inverse")

    # Show the capacities
    with st.expander("Production capacity"):
        production_capacity = stats.production_capacity(run_name, countries=selected_country_codes)
        cols = st.columns(max(len(production_capacity), 3))
        for index, technology in enumerate(production_capacity):
            cols[index].metric(utils.labelize_technology(technology), f"{int(production_capacity[technology] / 1000):,}GW")

    with st.expander("Storage capacity"):
        storage_capacity = stats.storage_capacity(run_name, type="energy", countries=selected_country_codes)
        cols = st.columns(max(len(storage_capacity), 3))
        for index, technology in enumerate(storage_capacity):
            technology_label = utils.labelize_technology(technology)
            cols[index].metric(f"{technology_label} energy", f"{storage_capacity[technology] / 10**6:.2f}TWh")
