import os
import pandas as pd
import gurobipy as gp
import streamlit as st
from datetime import datetime

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
    model = gp.Model("Name")

    """
    Step 2: Add the variables and constraints for each bidding zone
    """
    # Create dictionaries to store all the data per bidding zone
    hourly_results = {}
    production_capacity = {}
    storage_capacity = {}

    # Create a progress bar
    bidding_zones_count = sum(len(country["zones"]) for country in config["countries"])
    initialized_bidding_zones_count = 0
    progress = st.progress(0)

    for country in config["countries"]:
        for bidding_zone in country["zones"]:
            # Initialize the bidding zone

            """
            Step 2A: Import the hourly data
            """
            filepath = f"../input/bidding_zones/{config['model_year']}/{bidding_zone}.csv"
            start_date = config["date_range"]["start"]
            end_date = config["date_range"]["end"]
            hourly_data = utils.read_hourly_data(filepath, start=start_date, end=end_date)
            hourly_results[bidding_zone] = hourly_data.loc[:, ["demand_MWh"]]

            """
            Step 2B: Define production capacity variables
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

                    hourly_results[bidding_zone][f"production_{production_technology}_MWh"] = hourly_data.apply(calculate_hourly_production, args=(capacity,), axis=1)
                    hourly_results[bidding_zone]["total_production_MWh"] += hourly_results[bidding_zone][f"production_{production_technology}_MWh"]

            """
            Step 2C: Define storage variables and constraints
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
                    soc = model.addVars(hourly_data.index, lb=assumptions["soc_min"], ub=assumptions["soc_max"])

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
                        hourly_results[bidding_zone].loc[timestamp, "net_storage_flow_MWh"] += net_flow
                        hourly_results[bidding_zone].loc[timestamp, "energy_stored_MWh"] += soc_current * energy_capacity

                        # Update the previous_timestamp
                        previous_timestamp = timestamp

            """
            Step 2D: Define demand constraints
            """
            with st.spinner("Adding demand constraints"):
                hourly_results[bidding_zone].apply(lambda row: model.addConstr(row.total_production_MWh - row.net_storage_flow_MWh >= row.demand_MWh), axis=1)

            # Update the progress bar
            initialized_bidding_zones_count += 1
            progress.progress(initialized_bidding_zones_count / bidding_zones_count)

    """
    Step 3: Set objective function
    """
    firm_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_results)
    model.setObjective(firm_lcoe, gp.GRB.MINIMIZE)

    """
    Step 4: Solve model
    """
    with st.spinner(f"Optimizing"):
        start_optimizing = datetime.now()

        # Run model
        model.setParam("OutputFlag", 0)
        model.setParam("NonConvex", 2)
        model.optimize()

        # Show success or error message
        if model.status == gp.GRB.OPTIMAL:
            duration = datetime.now() - start_optimizing
            st.success(f"Optimization finished succesfully in {duration}")
        else:
            st.error("The model could not be resolved")
            return

    """
    Step 5: Store the results
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_folder = f"../output/{timestamp}"
    os.makedirs(f"{output_folder}/bidding_zones", exist_ok=True)

    # Store the actual values per bidding zone for the hourly results
    for bidding_zone, hourly_results in hourly_results.items():
        hourly_results = utils.convert_variables_recursively(hourly_results)
        hourly_results["curtailed_MWh"] = hourly_results.total_production_MWh - hourly_results.demand_MWh - hourly_results.net_storage_flow_MWh
        hourly_results.to_csv(f"{output_folder}/bidding_zones/{bidding_zone}.csv")

    # Store the actual values for the production capacity
    production_capacity = utils.convert_variables_recursively(production_capacity)
    utils.store_yaml(f"{output_folder}/production.yaml", production_capacity)

    # Store the actual values for the storage capacity
    storage_capacity = utils.convert_variables_recursively(storage_capacity)
    utils.store_yaml(f"{output_folder}/storage.yaml", storage_capacity)
    utils.store_yaml(f"{output_folder}/config.yaml", config)
