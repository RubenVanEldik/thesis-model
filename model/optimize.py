import pandas as pd
import gurobipy as gp
import streamlit as st
from datetime import datetime
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
    return data[range[0] : range[1]]


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

    return pv_production + onshore_production + offshore_production >= data.demand_MWh


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
            Step 2: Define variables
            """
            climate_zones = get_climate_zones(year, bidding_zone)

            # Add production capacity variables
            capacity_per_technology = {
                "pv": model.addVars(climate_zones["pv"]),
                "onshore": model.addVars(climate_zones["onshore"]),
                "offshore": model.addVars(climate_zones["offshore"]),
            }

            """
            Step 3: Add constraints
            """
            hourly_data = get_hourly_data(year, bidding_zone, range=data_range)
            with st.spinner("Adding demand constraints"):
                model.addConstrs(
                    create_demand_constraint(hourly_data.loc[timestamp], capacity_per_technology)
                    for timestamp in hourly_data.index
                )

            """
            Step 4: Set objective function
            """
            total_capacity_per_technology = {
                "pv": sum_all_climate_zones(capacity_per_technology["pv"]),
                "onshore": sum_all_climate_zones(capacity_per_technology["onshore"]),
                "offshore": sum_all_climate_zones(capacity_per_technology["offshore"]),
            }

            with st.spinner("Preparing LCOE objective"):
                obj = lcoe.calculate(total_capacity_per_technology, hourly_data.demand_MWh, year)
                model.setObjective(obj, gp.GRB.MINIMIZE)

            """
            Step 5: Solve model
            """
            with st.spinner(f"Optimizing for {bidding_zone}"):
                start_optimizing = datetime.now()

                # Run model
                model.setParam("OutputFlag", 0)
                model.optimize()

                # Show success or error message
                if model.status == gp.GRB.OPTIMAL:
                    duration = datetime.now() - start_optimizing
                    message = f"Optimization for {bidding_zone} finished succesfully in {duration}"
                    st.success(message)
                else:
                    st.error("The model could not be resolved")

            """
            Step 6: Get the final values of the variables
            """
            installed_pv = sum(retrieve_variables(model, capacity_per_technology["pv"]))
            installed_onshore = sum(retrieve_variables(model, capacity_per_technology["onshore"]))
            installed_offshore = sum(retrieve_variables(model, capacity_per_technology["offshore"]))

            """
            Step 7: Show results
            """
            col1, col2, col3 = st.columns(3)
            col1.metric("Solar PV", f"{int(installed_pv / 1000):,}GW")
            col2.metric("Onshore wind", f"{int(installed_onshore / 1000):,}GW")
            col3.metric("Offshore wind", f"{int(installed_offshore / 1000):,}GW")
