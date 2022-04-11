import os
import pandas as pd
import gurobipy as gp
import streamlit as st
from datetime import datetime, timedelta

import lcoe
import utils
import technologies
import validate


def run(config):
    """
    Create and run the model
    """
    assert validate.is_config(config)

    """
    Step 1: Create the model
    """
    status_message = st.empty()
    model = gp.Model("Name")

    """
    Step 2: Create a bidding zone list and set the progress bar
    """
    bidding_zones = []
    for country in config["countries"]:
        bidding_zones += country["zones"]
    progress = st.progress(0)

    """
    Step 3: Initialize each bidding zone
    """
    # Create dictionaries to store all the data per bidding zone
    hourly_results = {}
    production_capacity = {}
    storage_capacity = {}
    interconnections = {}

    for index, bidding_zone in enumerate(bidding_zones):
        """
        Step 3A: Import the hourly data
        """
        with st.spinner(f"Importing data for {bidding_zone}"):
            filepath = f"../input/bidding_zones/{config['model_year']}/{bidding_zone}.csv"
            start_date = config["date_range"]["start"]
            end_date = config["date_range"]["end"]
            hourly_data = utils.read_hourly_data(filepath, start=start_date, end=end_date)
            hourly_results[bidding_zone] = hourly_data.loc[:, ["demand_MWh"]]

            # Create empty DataFrames for the interconnections, if they don't exist yet
            if not len(interconnections):
                interconnections["hvac"] = pd.DataFrame(index=hourly_results[bidding_zone].index)
                interconnections["hvdc"] = pd.DataFrame(index=hourly_results[bidding_zone].index)

        """
        Step 3B: Define production capacity variables
        """
        production_capacity[bidding_zone] = {}
        hourly_results[bidding_zone]["total_production_MWh"] = 0
        with st.spinner(f"Adding production to {bidding_zone}"):
            for production_technology in technologies.technology_types("production"):
                climate_zones = [column for column in hourly_data.columns if column.startswith(f"{production_technology}_")]
                capacity = model.addVars(climate_zones)
                capacity_sum = gp.quicksum(capacity.values())
                production_capacity[bidding_zone][production_technology] = capacity_sum

                def calculate_hourly_production(row, capacities):
                    return sum(row[climate_zone] * capacity for climate_zone, capacity in capacities.items())

                column_name = f"production_{production_technology}_MWh"
                hourly_results[bidding_zone][column_name] = hourly_data.apply(calculate_hourly_production, args=(capacity,), axis=1)
                hourly_results[bidding_zone]["total_production_MWh"] += hourly_results[bidding_zone][column_name]

        """
        Step 3C: Define storage variables and constraints
        """
        # Create an object to save the storage capacity (energy & power) and add 2 columns to the results DataFrame
        storage_capacity[bidding_zone] = {}
        hourly_results[bidding_zone]["net_storage_flow_MWh"] = 0
        hourly_results[bidding_zone]["energy_stored_MWh"] = 0
        with st.spinner(f"Adding storage to {bidding_zone}"):
            # Add the variables and constraints for all storage technologies
            for storage_technology in technologies.technology_types("storage"):
                # Get the specific storage assumptions
                assumptions = technologies.assumptions("storage", storage_technology)

                # Create a variable for the energy and power storage capacity
                storage_capacity[bidding_zone][storage_technology] = {
                    "energy": model.addVar(),
                    "power": model.addVar(),
                }

                # Create the hourly state of charge variables
                energy_stored_hourly = model.addVars(hourly_data.index)

                # Create the hourly inflow and outflow variables
                inflow = model.addVars(hourly_data.index)
                outflow = model.addVars(hourly_data.index)

                # Loop over all hours
                previous_timestamp = None
                for timestamp in hourly_data.index:
                    # Unpack the energy and power capacities
                    energy_capacity = storage_capacity[bidding_zone][storage_technology]["energy"]
                    power_capacity = storage_capacity[bidding_zone][storage_technology]["power"]

                    # Get the previous state of charge and one-way efficiency
                    energy_stored_current = energy_stored_hourly[timestamp]
                    energy_stored_previous = energy_stored_hourly.get(previous_timestamp, assumptions["soc0"] * energy_capacity)
                    efficiency = assumptions["roundtrip_efficiency"] ** 0.5

                    # Add the state of charge constraints
                    model.addConstr(energy_stored_current == energy_stored_previous + (inflow[timestamp] * efficiency - outflow[timestamp] / efficiency))

                    # Add the energy capacity constraints (can't be added when the flow variables are defined because it's a gurobipy.Var)
                    model.addConstr(energy_stored_hourly[timestamp] >= assumptions["soc_min"] * energy_capacity)
                    model.addConstr(energy_stored_hourly[timestamp] <= assumptions["soc_max"] * energy_capacity)

                    # Add the power capacity constraints (can't be added when the flow variables are defined because it's a gurobipy.Var)
                    model.addConstr(inflow[timestamp] <= power_capacity)
                    model.addConstr(outflow[timestamp] <= power_capacity)

                    # Add the net flow to the total net storage
                    net_flow = inflow[timestamp] - outflow[timestamp]
                    hourly_results[bidding_zone].loc[timestamp, "net_storage_flow_MWh"] += net_flow
                    hourly_results[bidding_zone].loc[timestamp, "energy_stored_MWh"] += energy_stored_current

                    # Update the previous_timestamp
                    previous_timestamp = timestamp

        """
        Step 3D: Define the interconnection variables
        """

        def add_interconnection(timestamp, *, limits, model_year, model):
            interconnection_timestamp = timestamp.replace(year=model_year)
            limit = limits.loc[interconnection_timestamp]
            return model.addVar(ub=limit)

        with st.spinner(f"Adding interconnections to {bidding_zone}"):
            for connection_type in ["hvac", "hvdc"]:
                interconnection_limits = utils.get_interconnections(bidding_zone, type=connection_type, config=config)
                for column in interconnection_limits:
                    interconnection_limit = interconnection_limits[column]
                    interconnection_index = interconnections[connection_type].index.to_series()
                    interconnections[connection_type][column] = interconnection_index.apply(add_interconnection, limits=interconnection_limit, model_year=config["model_year"], model=model)

        """
        Step 3E: Update the progress bar
        """
        progress.progress((index + 1) / len(bidding_zones))

    """
    Step 4: Define demand constraints
    """
    for bidding_zone in bidding_zones:
        with st.spinner(f"Adding demand constraints to {bidding_zone}"):
            # Add a column for the hourly export to each country
            for type in interconnections:
                relevant_interconnections = [interconnection for interconnection in interconnections[type] if bidding_zone in interconnection]
                for interconnection in relevant_interconnections:
                    direction = 1 if interconnection[0] == bidding_zone else -1
                    other_bidding_zone = interconnection[1 if interconnection[0] == bidding_zone else 0]
                    column_name = f"net_export_{other_bidding_zone}_MWh"
                    if column_name not in hourly_results:
                        hourly_results[bidding_zone][column_name] = 0
                    hourly_results[bidding_zone][column_name] += direction * interconnections[type][interconnection]
            hourly_results[bidding_zone]["net_export_MWh"] = 0

            # Add a column for the total hourly export
            for column_name in hourly_results[bidding_zone]:
                if column_name.startswith("net_export_") and column_name != "net_export_MWh":
                    hourly_results[bidding_zone]["net_export_MWh"] += hourly_results[bidding_zone][column_name]

            # Add the demand constraint
            hourly_results[bidding_zone].apply(lambda row: model.addConstr(row.total_production_MWh - row.net_storage_flow_MWh - row.net_export_MWh >= row.demand_MWh), axis=1)

    """
    Step 5: Set objective function
    """
    firm_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results)
    model.setObjective(firm_lcoe, gp.GRB.MINIMIZE)

    """
    Step 6: Solve model
    """
    with st.spinner(f"Optimizing"):

        # Run model
        model.setParam("OutputFlag", 0)
        model.optimize()

        # Show success or error message
        if model.status == gp.GRB.OPTIMAL:
            status_message.success(f"Optimization finished succesfully in {timedelta(seconds=model.Runtime)}")
            progress.empty()
        else:
            st.error("The model could not be resolved")
            return

    """
    Step 7: Store the results
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_folder = f"../output/{timestamp}"
    os.makedirs(f"{output_folder}/bidding_zones", exist_ok=True)

    # Store the actual values per bidding zone for the hourly results
    for bidding_zone, hourly_results in hourly_results.items():
        hourly_results = utils.convert_variables_recursively(hourly_results)
        hourly_results["curtailed_MWh"] = hourly_results.total_production_MWh - hourly_results.demand_MWh - hourly_results.net_storage_flow_MWh - hourly_results.net_export_MWh
        hourly_results.to_csv(f"{output_folder}/bidding_zones/{bidding_zone}.csv")

    # Store the actual values for the production capacity
    production_capacity = utils.convert_variables_recursively(production_capacity)
    utils.store_yaml(f"{output_folder}/production.yaml", production_capacity)

    # Store the actual values for the storage capacity
    storage_capacity = utils.convert_variables_recursively(storage_capacity)
    utils.store_yaml(f"{output_folder}/storage.yaml", storage_capacity)
    utils.store_yaml(f"{output_folder}/config.yaml", config)
