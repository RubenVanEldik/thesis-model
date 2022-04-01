import pandas as pd
import gurobipy as gp
import streamlit as st
from datetime import datetime
import technologies
import lcoe


@st.experimental_memo
def get_hourly_data(year, bidding_zone, *, range=None, only_headers=False):
    """
    Return the hourly data for a specific model year and bidding zone
    """
    data = pd.read_csv(
        f"../input/bidding_zones/{year}/{bidding_zone}.csv",
        parse_dates=True,
        index_col=0,
        nrows=0 if only_headers else None,
    )

    if not range:
        return data
    return data[range[0].strftime("%Y-%m-%d 00:00:00") : range[1].strftime("%Y-%m-%d 23:59:59")]


def get_climate_zones(year, bidding_zone):
    """
    Return an object with the climate zone names for wind and PV
    """
    columns = get_hourly_data(year, bidding_zone, only_headers=True).columns

    return {
        "pv": [column for column in columns if column.startswith("pv")],
        "onshore": [column for column in columns if column.startswith("onshore")],
        "offshore": [column for column in columns if column.startswith("offshore")],
    }


def sum_all_climate_zones(climate_zones, *, func=None):
    """
    Return the sum of all climate zones, if a function is defined it will be used to calculate the value
    """
    if func is None:
        return gp.quicksum(climate_zone for climate_zone in climate_zones.values())
    return gp.quicksum(func(climate_zone, column) for column, climate_zone in climate_zones.items())


def retrieve_variables(model, variables):
    """
    Retrieve the value of the variables after the model has been run
    """
    return model.getAttr("x", variables).values()


def create_demand_constraint(data, capacity):
    """
    Return an object with the climate zone names for wind and PV
    """
    calculate_output = lambda capacity, climate_zone: capacity * data[climate_zone]

    pv_production = sum_all_climate_zones(capacity["pv"], func=calculate_output)
    onshore_production = sum_all_climate_zones(capacity["onshore"], func=calculate_output)
    offshore_production = sum_all_climate_zones(capacity["offshore"], func=calculate_output)
    total_production = pv_production + onshore_production + offshore_production

    return total_production - data.net_storage_flow >= data.demand_MWh


def run(year, countries, data_range):
    """
    Run the model!
    """
    for country in countries:
        for bidding_zone in country["zones"]:
            """
            Step 1: Create a model
            """
            model = gp.Model("Name")

            """
            Step 2: Define production variables
            """
            hourly_data = get_hourly_data(year, bidding_zone, range=data_range)
            climate_zones = get_climate_zones(year, bidding_zone)

            # Add production capacity variables
            capacity_per_technology = {
                "pv": model.addVars(climate_zones["pv"]),
                "onshore": model.addVars(climate_zones["onshore"]),
                "offshore": model.addVars(climate_zones["offshore"]),
            }

            """
            Step 3: Define storage variables and constraints
            """
            # Create an object to save the storage capacity (energy & power)
            # and add a column to the DataFrame to store the hourly net storage flow
            storage_capacity = {}
            hourly_data["net_storage_flow"] = 0
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
                soc_min = assumptions["soc_min"]
                soc_max = assumptions["soc_max"]
                soc = model.addVars(hourly_data.index, lb=soc_min, ub=soc_max)

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
                    soc_previous = soc.get(previous_timestamp, assumptions["soc0"])
                    efficiency = assumptions["roundtrip_efficiency"] ** 0.5

                    # Add the state of charge constraints
                    model.addConstr(
                        soc[timestamp] * energy_capacity
                        == soc_previous * energy_capacity
                        + (inflow[timestamp] * efficiency - outflow[timestamp] / efficiency)
                    )

                    # Add the power capacity constraints
                    model.addConstr(inflow[timestamp] <= power_capacity)
                    model.addConstr(outflow[timestamp] <= power_capacity)

                    # Add the net flow to the total net storage
                    net_flow = inflow[timestamp] - outflow[timestamp]
                    hourly_data.loc[timestamp, "net_storage_flow"] += net_flow

                    # Update the previous_timestamp
                    previous_timestamp = timestamp

            """
            Step 4: Define demand constraints
            """
            with st.spinner("Adding demand constraints"):
                model.addConstrs(
                    create_demand_constraint(hourly_data.loc[timestamp], capacity_per_technology)
                    for timestamp in hourly_data.index
                )

            """
            Step 5: Set objective function
            """
            production_capacity = {
                "pv": sum_all_climate_zones(capacity_per_technology["pv"]),
                "onshore": sum_all_climate_zones(capacity_per_technology["onshore"]),
                "offshore": sum_all_climate_zones(capacity_per_technology["offshore"]),
            }

            obj = lcoe.calculate(
                production_capacity, storage_capacity, hourly_data.demand_MWh, year
            )
            model.setObjective(obj, gp.GRB.MINIMIZE)

            """
            Step 6: Solve model
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
                    message = f"Optimization for {bidding_zone} finished succesfully in {duration}"
                    st.success(message)
                else:
                    st.error("The model could not be resolved")
                    return

            """
            Step 7: Get the final values of the variables
            """
            final_lcoe = model.getObjective().getValue()
            installed_pv = sum(retrieve_variables(model, capacity_per_technology["pv"]))
            installed_onshore = sum(retrieve_variables(model, capacity_per_technology["onshore"]))
            installed_offshore = sum(retrieve_variables(model, capacity_per_technology["offshore"]))
            installed_lion = storage_capacity["lion"]["energy"].X

            """
            Step 8: Show results
            """
            st.subheader("Key performance indicators")
            col1, col2, col3 = st.columns(3)
            col1.metric("LCOE", f"{int(final_lcoe)}€/MWh")
            col2.metric("Firm kWh premium", "-")
            col3.metric("Curtailment", "-")

            st.subheader("Generation capacity")
            col1, col2, col3 = st.columns(3)
            col1.metric("Solar PV", f"{int(installed_pv / 1000):,}GW")
            col2.metric("Onshore wind", f"{int(installed_onshore / 1000):,}GW")
            col3.metric("Offshore wind", f"{int(installed_offshore / 1000):,}GW")

            st.subheader("Storage capacity")
            col1, col2, col3 = st.columns(3)
            col1.metric("Li-ion", f"{int(installed_lion / 1000):,}GWh")
            col2.metric("Pumped hydro", "-")
            col3.metric("Hydrogen", "-")
