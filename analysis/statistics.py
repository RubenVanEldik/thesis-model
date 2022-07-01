import streamlit as st

import stats
import utils
import validate


def statistics(run_name, resolution):
    """
    Show the key indicators for a run
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)

    st.title("📊 Statistics")

    st.sidebar.header("Options")

    # Ask for which countries the statistics should be shown
    config = utils.read_yaml(f"./output/{run_name}/config.yaml")
    selected_countries = st.sidebar.multiselect("Countries", config["countries"], format_func=lambda country: country["name"])
    selected_country_codes = [country["nuts_2"] for country in selected_countries]

    # Calculate the mean demand over all selected countries
    temporal_results = utils.get_temporal_results(run_name, resolution, countries=selected_country_codes)
    mean_demand = utils.merge_dataframes_on_column(temporal_results, "demand_MW").sum(axis=1).mean()

    # Show the KPI's
    with st.expander("KPI's", expanded=True):
        col1, col2, col3 = st.columns(3)

        # LCOE
        firm_lcoe_selected = stats.firm_lcoe(run_name, resolution, countries=selected_country_codes)
        firm_lcoe_all = stats.firm_lcoe(run_name, resolution)
        lcoe_delta = f"{(firm_lcoe_selected / firm_lcoe_all) - 1:.0%}" if selected_country_codes else None
        col1.metric("LCOE", f"{int(firm_lcoe_selected)}€/MWh", lcoe_delta, delta_color="inverse")

        # Firm kWh premium
        premium_selected = stats.premium(run_name, resolution, countries=selected_country_codes)
        premium_all = stats.premium(run_name, resolution)
        premium_delta = f"{(premium_selected / premium_all) - 1:.0%}" if selected_country_codes else None
        col2.metric("Firm kWh premium", f"{premium_selected:.2f}", premium_delta, delta_color="inverse")

        # Curtailment
        curtailment_selected = stats.relative_curtailment(run_name, resolution, countries=selected_country_codes)
        curtailment_all = stats.relative_curtailment(run_name, resolution)
        curtailment_delta = f"{(curtailment_selected / curtailment_all) - 1:.0%}" if selected_country_codes else None
        col3.metric("Curtailment", f"{curtailment_selected:.1%}", curtailment_delta, delta_color="inverse")

    # Show the production capacities
    with st.expander("Production capacity", expanded=True):
        # Ask if the results should be shown relative to the mean demand
        show_relative_production_capacity = st.checkbox("Relative to demand", value=True, key="production")
        show_hourly_production = st.checkbox("Mean hourly production")

        # Get the production capacities
        production_capacity = stats.production_capacity(run_name, resolution, countries=selected_country_codes)

        # Create the storage capacity columns
        cols = st.columns(max(len(production_capacity), 3))

        # Create the metric for each production technology
        for index, technology in enumerate(production_capacity):
            # Set the metric value depending on the checkboxes
            if show_hourly_production:
                mean_hourly_production = utils.merge_dataframes_on_column(temporal_results, f"production_{technology}_MW").sum(axis=1).mean()
                if show_relative_production_capacity:
                    metric_value = f"{mean_hourly_production / mean_demand:.1%}"
                else:
                    metric_value = f"{mean_hourly_production / 1000:,.0f}GW"
            else:
                if show_relative_production_capacity:
                    metric_value = f"{production_capacity[technology] / mean_demand:.1%}"
                else:
                    metric_value = f"{production_capacity[technology] / 1000:,.0f}GW"

            # Set the metric
            cols[index].metric(utils.labelize_technology(technology), metric_value)

    # Show the storage capacities
    with st.expander("Storage capacity", expanded=True):
        # Ask if the results should be shown relative to the mean demand
        show_relative_storage_capacity = st.checkbox("Relative to demand", value=True, key="storage")
        show_power_capacity = st.checkbox("Power capacity")
        storage_type = "power" if show_power_capacity else "energy"

        # Get the storage capacities
        storage_capacity = stats.storage_capacity(run_name, resolution, type=storage_type, countries=selected_country_codes)

        # Create the storage capacity columns
        cols = st.columns(max(len(storage_capacity), 3))

        # Create the metric for each storage technology
        for index, technology in enumerate(storage_capacity):
            # Set the metric value depending on the checkbox
            if show_power_capacity:
                if show_relative_storage_capacity:
                    metric_value = f"{storage_capacity[technology] / mean_demand:.1%}"
                else:
                    metric_value = f"{storage_capacity[technology] / 1000:,.0f}MW"
            else:
                if show_relative_storage_capacity:
                    metric_value = f"{storage_capacity[technology] / mean_demand:.2f}H"
                else:
                    metric_value = f"{storage_capacity[technology] / 1000:,.0f}MWh"

            # Set the metric
            cols[index].metric(f"{utils.labelize_technology(technology)} {storage_type}", metric_value)
