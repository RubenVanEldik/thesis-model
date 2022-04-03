import pandas as pd
import gurobipy as gp
import streamlit as st
from datetime import datetime
import validate
import technologies
import lcoe


@st.experimental_memo
def _get_hourly_data(year, bidding_zone, *, range=None):
    """
    Return the hourly data for a specific model year and bidding zone
    """
    assert validate.is_model_year(year)
    assert validate.is_bidding_zone(bidding_zone)
    assert validate.is_date_range(range, required=False)

    filepath = f"../input/bidding_zones/{year}/{bidding_zone}.csv"
    data = pd.read_csv(filepath, parse_dates=True, index_col=0)

    if not range:
        return data
    return data[range[0].strftime("%Y-%m-%d 00:00:00") : range[1].strftime("%Y-%m-%d 23:59:59")]


def _calculate_hourly_production(row, capacities):
    """
    Return the production in a specific hour for a specific technology
    """
    assert validate.is_hourly_data_row(row)
    assert validate.is_climate_zone_dict(capacities)

    total_production_MWh = 0
    for climate_zone, capacity in capacities.items():
        total_production_MWh += row[climate_zone] * capacity
    return total_production_MWh


def run(year, countries, date_range):
    """
    Run the model!
    """
    assert validate.is_model_year(year)
    assert validate.is_country_obj_list(countries)
    assert validate.is_date_range(date_range)

    for country in countries:
        for bidding_zone in country["zones"]:
            """
            Step 1: Create a model
            """
            model = gp.Model("Name")

            """
            Step 2: Create an hourly_data and hourly_results DataFrame
            """
            hourly_data = _get_hourly_data(year, bidding_zone, range=date_range)
            hourly_results = hourly_data[["demand_MWh"]]

            """
            Step 3: Define production capacity variables
            """
            production_capacity = {}
            hourly_results["total_production_MWh"] = 0
            for production_technology in technologies.technology_types("production"):
                climate_zones = [column for column in hourly_data.columns if column.startswith(f"{production_technology}_")]
                capacity = model.addVars(climate_zones)
                capacity_sum = gp.quicksum(capacity.values())
                production_capacity[production_technology] = capacity_sum
                hourly_results[f"production_{production_technology}_MWh"] = hourly_data.apply(_calculate_hourly_production, args=(capacity,), axis=1)
                hourly_results["total_production_MWh"] += hourly_results[f"production_{production_technology}_MWh"]

            """
            Step 4: Define storage variables and constraints
            """
            # Create an object to save the storage capacity (energy & power) and add 2 columns to the results DataFrame
            storage_capacity = {}
            hourly_results["net_storage_flow_MWh"] = 0
            hourly_results["energy_stored_MWh"] = 0
            # Add the variables and constraints for all storage technologies
            for storage_technology in technologies.technology_types("storage"):
                # Get the specific storage assumptions
                assumptions = technologies.assumptions("storage", storage_technology)

                # Create a variable for the energy and power storage capacity
                storage_capacity[storage_technology] = {
                    "energy": model.addVar(),
                    "power": model.addVar(),
                }

                # Create the hourly state of charge variables
                soc = model.addVars(hourly_data.index, lb=assumptions["soc_min"], ub=assumptions["soc_max"])

                # Create the hourly inflow and outflow variables
                inflow = model.addVars(hourly_data.index)
                outflow = model.addVars(hourly_data.index)

                # Loop over all hours
                previous_timestamp = None
                for timestamp in hourly_data.index:
                    # Unpack the energy and power capacities
                    energy_capacity = storage_capacity[storage_technology]["energy"]
                    power_capacity = storage_capacity[storage_technology]["power"]

                    # Get the previous state of charge and one-way efficiency
                    soc_current = soc[timestamp]
                    soc_previous = soc.get(previous_timestamp, assumptions["soc0"])
                    efficiency = assumptions["roundtrip_efficiency"] ** 0.5

                    # Add the state of charge constraints
                    model.addConstr(soc_current * energy_capacity == soc_previous * energy_capacity + (inflow[timestamp] * efficiency - outflow[timestamp] / efficiency))

                    # Add the power capacity constraints (can't be added when the flow variables are defined because it's a gurobipy.Var)
                    model.addConstr(inflow[timestamp] <= power_capacity)
                    model.addConstr(outflow[timestamp] <= power_capacity)

                    # Add the net flow to the total net storage
                    net_flow = inflow[timestamp] - outflow[timestamp]
                    hourly_results.loc[timestamp, "net_storage_flow_MWh"] += net_flow
                    hourly_results.loc[timestamp, "energy_stored_MWh"] += soc_current * energy_capacity

                    # Update the previous_timestamp
                    previous_timestamp = timestamp

            """
            Step 5: Define demand constraints
            """
            with st.spinner("Adding demand constraints"):
                hourly_results.apply(lambda row: model.addConstr(row.total_production_MWh - row.net_storage_flow_MWh >= row.demand_MWh), axis=1)

            """
            Step 6: Set objective function
            """
            obj = lcoe.calculate(production_capacity, storage_capacity, hourly_data.demand_MWh)
            model.setObjective(obj, gp.GRB.MINIMIZE)

            """
            Step 7: Solve model
            """
            with st.spinner(f"Optimizing for {bidding_zone}"):
                start_optimizing = datetime.now()

                # Run model
                model.setParam("OutputFlag", 0)
                model.setParam("NonConvex", 2)
                model.optimize()

                # Show success or error message
                if model.status == gp.GRB.OPTIMAL:
                    duration = datetime.now() - start_optimizing
                    st.success(f"Optimization for {bidding_zone} finished succesfully in {duration}")
                else:
                    st.error("The model could not be resolved")
                    return

            """
            Step 8: Get the final values for all cells in the hourly results DataFrame
            """
            for column_name in hourly_results:
                if hourly_results[column_name].dtype == "object":
                    hourly_results[column_name] = hourly_results[column_name].apply(lambda x: x.getValue())

            hourly_results["curtailed_MWh"] = hourly_results.total_production_MWh - hourly_results.demand_MWh - hourly_results.net_storage_flow_MWh

            """
            Step 9: Get the final values of the variables
            """
            final_lcoe = model.getObjective().getValue()
            relative_curtailment = hourly_results.curtailed_MWh.sum() / hourly_results.total_production_MWh.sum()
            installed_pv = production_capacity["pv"].getValue()
            installed_onshore = production_capacity["onshore"].getValue()
            installed_offshore = production_capacity["offshore"].getValue()
            installed_lion = storage_capacity["lion"]["energy"].X

            """
            Step 10: Show results
            """
            st.subheader("Key performance indicators")
            col1, col2, col3 = st.columns(3)
            col1.metric("LCOE", f"{int(final_lcoe)}€/MWh")
            col2.metric("Firm kWh premium", "-")
            col3.metric("Curtailment", f"{relative_curtailment:.1%}")

            st.subheader("Production capacity")
            col1, col2, col3 = st.columns(3)
            col1.metric("Solar PV", f"{int(installed_pv / 1000):,}GW")
            col2.metric("Onshore wind", f"{int(installed_onshore / 1000):,}GW")
            col3.metric("Offshore wind", f"{int(installed_offshore / 1000):,}GW")

            st.subheader("Storage capacity")
            col1, col2, col3 = st.columns(3)
            col1.metric("Li-ion", f"{int(installed_lion / 1000):,}GWh")
            col2.metric("Pumped hydro", "-")
            col3.metric("Hydrogen", "-")
