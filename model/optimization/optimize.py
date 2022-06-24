from datetime import timedelta
import gurobipy as gp
import os
import pandas as pd
import re
import streamlit as st

import utils
import validate

from .calculate_time_energy_stored import calculate_time_energy_stored
from .intialize_model import intialize_model


def optimize(config, *, resolution, previous_resolution, status, output_folder):
    """
    Create and run the model
    """
    assert validate.is_config(config, new_config=True)
    assert validate.is_resolution(resolution)
    assert validate.is_resolution(previous_resolution, required=False)
    assert validate.is_directory_path(output_folder)

    """
    Step 1: Create the model and set the parameters
    """
    model = intialize_model(config)

    """
    Step 2: Create a bidding zone list and set the progress bar
    """
    bidding_zones = [bidding_zone for country in config["countries"] for bidding_zone in country["bidding_zones"]]
    progress = st.progress(0)

    """
    Step 3: Initialize each bidding zone
    """
    # Create dictionaries to store all the data per bidding zone
    temporal_data = {}
    temporal_results = {}
    production_capacity = {}
    storage_capacity = {}
    interconnections = {}

    for index, bidding_zone in enumerate(bidding_zones):
        """
        Step 3A: Import the temporal data
        """
        status.update(f"Importing data for {bidding_zone}")
        filepath = f"./input/bidding_zones/{config['model_year']}/{bidding_zone}.csv"
        start_date = config["date_range"]["start"]
        end_date = config["date_range"]["end"]
        # Get the temporal data and resample to the required resolution
        temporal_data[bidding_zone] = utils.read_temporal_data(filepath, start=start_date, end=end_date).resample(resolution).mean()
        # Remove the leap days from the dataset that could have been introduced by the resample method
        temporal_data[bidding_zone] = temporal_data[bidding_zone][~((temporal_data[bidding_zone].index.month == 2) & (temporal_data[bidding_zone].index.day == 29))]
        # Create an temporal_results DataFrame with the demand_MW column
        temporal_results[bidding_zone] = temporal_data[bidding_zone].loc[:, ["demand_MW"]]

        # Create a DataFrame for the production capacities
        production_capacity[bidding_zone] = pd.DataFrame(columns=config["technologies"]["production"].keys())

        if previous_resolution:
            # Get the temporal results from the previous run
            previous_temporal_results = utils.read_csv(f"{output_folder}/{previous_resolution}/temporal/{bidding_zone}.csv", parse_dates=True, index_col=0)
            # Resample the previous results so it has the same timestamps as the current step
            previous_temporal_results = previous_temporal_results.resample(resolution).mean()
            # Find and add the rows that are missing in the previous results (the resample method does not add rows after the last timestamp)
            for timestamp in temporal_results[bidding_zone].index.difference(previous_temporal_results.index):
                previous_temporal_results.loc[timestamp] = None
            # Remove all rows that are in previous_temporal_results but not in the new temporal_results DataFrame (don't know why this happens, but it happens sometimes)
            previous_temporal_results = previous_temporal_results[previous_temporal_results.index.isin(temporal_results[bidding_zone].index)]
            # Fill the empty rows created by the resample method by the value from the previous rows
            previous_temporal_results = previous_temporal_results.ffill()
            # Remove the leap days from the dataset that could have been introduced by the resample method
            previous_temporal_results = previous_temporal_results[~((previous_temporal_results.index.month == 2) & (previous_temporal_results.index.day == 29))]

        # Create empty DataFrames for the interconnections, if they don't exist yet
        if not len(interconnections):
            interconnections["hvac"] = pd.DataFrame(index=temporal_results[bidding_zone].index)
            interconnections["hvdc"] = pd.DataFrame(index=temporal_results[bidding_zone].index)

        """
        Step 3B: Define production capacity variables
        """
        temporal_results[bidding_zone]["production_total_MW"] = 0
        for production_technology in config["technologies"]["production"]:
            # Create a capacity variable for each climate zone
            climate_zones = [re.match(f"{production_technology}_(.+)_cf", column).group(1) for column in temporal_data[bidding_zone].columns if column.startswith(f"{production_technology}_")]
            if previous_resolution:
                previous_production_capacity = utils.read_csv(f"{output_folder}/{previous_resolution}/production/{bidding_zone}.csv", index_col=0)
                capacities = model.addVars(climate_zones, lb=config["time_discretization"]["capacity_propagation"] * previous_production_capacity[production_technology].dropna())
            else:
                capacities = model.addVars(climate_zones)

            # Add the capacities to the production_capacity DataFrame
            for climate_zone in capacities:
                production_capacity[bidding_zone].loc[climate_zone, production_technology] = capacities[climate_zone]

            # Calculate the temporal production for a specific technology
            def calculate_production_in_row(row, production_technology, capacities):
                status.update(f"Adding {utils.labelize_technology(production_technology, capitalize=False)} production to {bidding_zone}", timestamp=row.name)
                return sum(row[f"{production_technology}_{climate_zone}_cf"] * capacity for climate_zone, capacity in capacities.items())

            # Calculate the temporal production and add it to the temporal_results DataFrame
            temporal_production = temporal_data[bidding_zone].apply(calculate_production_in_row, args=(production_technology, capacities), axis=1)
            temporal_results[bidding_zone][f"production_{production_technology}_MW"] = temporal_production
            temporal_results[bidding_zone]["production_total_MW"] += temporal_production

        """
        Step 3C: Define storage variables and constraints
        """
        # Create a DataFrame for the storage capacity in this bidding zone
        storage_capacity[bidding_zone] = pd.DataFrame(0, index=config["technologies"]["storage"], columns=["energy", "power"])

        # Create an object to save the storage capacity (energy & power) and add 2 columns to the results DataFrame
        temporal_results[bidding_zone]["net_storage_flow_total_MW"] = 0
        temporal_results[bidding_zone]["energy_stored_total_MWh"] = 0

        # Add the variables and constraints for all storage technologies
        for storage_technology in config["technologies"]["storage"]:
            # Get the specific storage assumptions
            assumptions = config["technologies"]["storage"][storage_technology]
            timestep_hours = pd.Timedelta(resolution).total_seconds() / 3600

            # Create a variable for the energy and power storage capacity
            if previous_resolution:
                previous_storage_capacity = utils.read_csv(f"{output_folder}/{previous_resolution}/storage/{bidding_zone}.csv", index_col=0)
                storage_capacity[bidding_zone].loc[storage_technology, "energy"] = model.addVar(lb=config["time_discretization"]["capacity_propagation"] * previous_storage_capacity.loc[storage_technology, "energy"])
                storage_capacity[bidding_zone].loc[storage_technology, "power"] = model.addVar(lb=config["time_discretization"]["capacity_propagation"] * previous_storage_capacity.loc[storage_technology, "power"])
            else:
                storage_capacity[bidding_zone].loc[storage_technology, "energy"] = model.addVar()
                storage_capacity[bidding_zone].loc[storage_technology, "power"] = model.addVar()

            # Create the inflow and outflow variables
            if previous_resolution:
                inflow = model.addVars(temporal_data[bidding_zone].index, lb=config["time_discretization"]["soc_propagation"] * previous_temporal_results[f"net_storage_flow_{storage_technology}_MW"].clip(lower=0))
                outflow = model.addVars(temporal_data[bidding_zone].index, lb=config["time_discretization"]["soc_propagation"] * -previous_temporal_results[f"net_storage_flow_{storage_technology}_MW"].clip(upper=0))
            else:
                inflow = model.addVars(temporal_data[bidding_zone].index)
                outflow = model.addVars(temporal_data[bidding_zone].index)

            # Add the net storage flow variables to the temporal_results DataFrame
            net_flow = pd.Series(data=[inflow_value - outflow_value for inflow_value, outflow_value in zip(inflow.values(), outflow.values())], index=temporal_results[bidding_zone].index)
            temporal_results[bidding_zone][f"net_storage_flow_{storage_technology}_MW"] = net_flow
            temporal_results[bidding_zone]["net_storage_flow_total_MW"] += net_flow

            # Create the energy stored column for this storage technology in the temporal_results DataFrame
            temporal_results[bidding_zone][f"energy_stored_{storage_technology}_MWh"] = None

            # Unpack the energy and power capacities for this storage technology
            energy_capacity = storage_capacity[bidding_zone].loc[storage_technology, "energy"]
            power_capacity = storage_capacity[bidding_zone].loc[storage_technology, "power"]

            # Loop over all hours
            previous_timestamp = None
            energy_stored_previous = assumptions["soc0"] * energy_capacity
            for timestamp in temporal_data[bidding_zone].index:
                status.update(f"Adding {utils.labelize_technology(storage_technology, capitalize=False)} storage to {bidding_zone}", timestamp=timestamp)

                # Create the state of charge variables
                if previous_resolution:
                    energy_stored_current = model.addVar(lb=config["time_discretization"]["soc_propagation"] * previous_temporal_results.loc[timestamp, f"energy_stored_{storage_technology}_MWh"])
                else:
                    energy_stored_current = model.addVar()

                # Add the current energy stored to the temporal results DataFrame
                temporal_results[bidding_zone].loc[timestamp, f"energy_stored_{storage_technology}_MWh"] = energy_stored_current

                # Add the state of charge constraints
                efficiency = assumptions["roundtrip_efficiency"] ** 0.5
                model.addConstr(energy_stored_current == energy_stored_previous + (inflow[timestamp] * efficiency - outflow[timestamp] / efficiency) * timestep_hours)

                # Add the energy capacity constraints (can't be added when the flow variables are defined because it's a gurobipy.Var)
                model.addConstr(energy_stored_current >= assumptions["soc_min"] * energy_capacity)
                model.addConstr(energy_stored_current <= assumptions["soc_max"] * energy_capacity)

                # Add the power capacity constraints (can't be added when the flow variables are defined because it's a gurobipy.Var)
                model.addConstr(inflow[timestamp] <= power_capacity)
                model.addConstr(outflow[timestamp] <= power_capacity)

                # Update previous_timestamp and energy_stored_previous
                previous_timestamp = timestamp
                energy_stored_previous = energy_stored_current

            # Add the energy stored for this storage technology to the total energy stored column
            temporal_results[bidding_zone]["energy_stored_total_MWh"] += temporal_results[bidding_zone][f"energy_stored_{storage_technology}_MWh"]

        """
        Step 3D: Define the interconnection variables
        """

        def add_interconnection(timestamp, *, limits, model_year, model):
            interconnection_timestamp = timestamp.replace(year=model_year)
            limit = limits.loc[interconnection_timestamp]
            return model.addVar(ub=limit)

        for connection_type in ["hvac", "hvdc"]:
            status.update(f"Adding {connection_type.upper()} interconnections to {bidding_zone}")
            interconnection_limits = utils.get_interconnections(bidding_zone, type=connection_type, config=config)
            for column in interconnection_limits:
                interconnection_limit = interconnection_limits[column] * config["interconnections"]["relative_capacity"]
                interconnection_index = interconnections[connection_type].index.to_series()
                interconnections[connection_type][column] = interconnection_index.apply(add_interconnection, limits=interconnection_limit, model_year=config["model_year"], model=model)

        # Update the progress bar
        progress.progress((index + 1) / len(bidding_zones))

    # Remove the progress bar
    progress.empty()

    """
    Step 4: Define demand constraints
    """
    for bidding_zone in bidding_zones:
        status.update(f"Adding demand constraints to {bidding_zone}")

        # Add a column for the temporal export to each country
        for interconnection_type in interconnections:
            relevant_interconnections = [interconnection for interconnection in interconnections[interconnection_type] if bidding_zone in interconnection]
            for interconnection in relevant_interconnections:
                direction = 1 if interconnection[0] == bidding_zone else -config["interconnections"]["efficiency"][interconnection_type]
                other_bidding_zone = interconnection[1 if interconnection[0] == bidding_zone else 0]
                column_name = f"net_export_{other_bidding_zone}_MW"
                if column_name not in temporal_results:
                    temporal_results[bidding_zone][column_name] = 0
                temporal_results[bidding_zone][column_name] += direction * interconnections[interconnection_type][interconnection]

        # Add a column for the total temporal export
        temporal_results[bidding_zone]["net_export_MW"] = 0
        for column_name in temporal_results[bidding_zone]:
            if column_name.startswith("net_export_") and column_name != "net_export_MW":
                temporal_results[bidding_zone]["net_export_MW"] += temporal_results[bidding_zone][column_name]

        # Add the demand constraint
        temporal_results[bidding_zone].apply(lambda row: model.addConstr(row.production_total_MW - row.net_storage_flow_total_MW - row.net_export_MW >= row.demand_MW), axis=1)

        # Calculate the curtailed energy per hour
        curtailed_MW = temporal_results[bidding_zone].production_total_MW - temporal_results[bidding_zone].demand_MW - temporal_results[bidding_zone].net_storage_flow_total_MW - temporal_results[bidding_zone].net_export_MW
        temporal_results[bidding_zone].insert(temporal_results[bidding_zone].columns.get_loc("production_total_MW"), "curtailed_MW", curtailed_MW)

    """
    Step 5: Set objective function
    """
    temporal_demand = utils.merge_dataframes_on_column(temporal_results, "demand_MW")
    firm_lcoe = utils.calculate_lcoe(production_capacity, storage_capacity, temporal_demand, config=config)
    model.setObjective(firm_lcoe, gp.GRB.MINIMIZE)

    """
    Step 6: Solve model
    """
    # Set the status message and create
    status.update("Optimizing")

    # Create the optimization log expander
    with st.expander(f"{utils.format_resolution(resolution)} resolution"):
        # Create three columns for statistics
        col1, col2, col3 = st.columns(3)
        stat1 = col1.empty()
        stat2 = col2.empty()
        stat3 = col3.empty()

        log_messages = []
        info = st.empty()

    def optimization_callback(model, where):
        """
        Show the intermediate results
        """
        if where == gp.GRB.Callback.BARRIER:
            iteration = model.cbGet(gp.GRB.Callback.BARRIER_ITRCNT)
            objective_value = model.cbGet(gp.GRB.Callback.BARRIER_PRIMOBJ)
            infeasibility = model.cbGet(gp.GRB.Callback.BARRIER_PRIMINF)
            stat1.metric("Iteration (barrier)", f"{iteration:,}")
            stat2.metric("Objective", f"{int(objective_value)}€/MWh")
            stat3.metric("Infeasibility", f"{infeasibility:.2E}")
        if where == gp.GRB.Callback.SIMPLEX and model.cbGet(gp.GRB.Callback.SPX_ITRCNT) % 1000 == 0:
            iteration = model.cbGet(int(gp.GRB.Callback.SPX_ITRCNT))
            objective_value = model.cbGet(gp.GRB.Callback.SPX_OBJVAL)
            infeasibility = model.cbGet(gp.GRB.Callback.SPX_PRIMINF)
            stat1.metric("Iteration (simplex)", f"{int(iteration):,}")
            stat2.metric("Objective", f"{int(objective_value)}€/MWh")
            stat3.metric("Infeasibility", f"{infeasibility:.2E}")
        if where == gp.GRB.Callback.MESSAGE:
            log_messages.append(model.cbGet(gp.GRB.Callback.MSG_STRING))
            info.code("".join(log_messages))

    # Run the model
    model.optimize(optimization_callback)

    # Show success or error message
    if model.status == gp.GRB.TIME_LIMIT:
        status.update(f"Optimization finished due to the time limit in {timedelta(seconds=model.Runtime)}", type="warning")
        return
    elif model.status != gp.GRB.OPTIMAL:
        status.update("The model could not be resolved", type="error")
        return

    """
    Step 7: Store the results
    """
    # Make a directory for each type of output
    for directory in ["temporal", "production", "storage"]:
        os.makedirs(f"{output_folder}/{resolution}/{directory}")

    # Store the actual values per bidding zone for the temporal results
    for bidding_zone in bidding_zones:
        status.update(f"Converting and storing the results for {bidding_zone}")
        # Convert the temporal results variables
        temporal_results_bidding_zone = utils.convert_variables_recursively(temporal_results[bidding_zone])

        # Calculate the time of energy stored per storage technology per hour
        for storage_technology in config["technologies"]["storage"]:
            time_stored_H = temporal_results_bidding_zone.apply(calculate_time_energy_stored, storage_technology=storage_technology, temporal_results=temporal_results_bidding_zone, axis=1)
            column_index = temporal_results_bidding_zone.columns.get_loc(f"energy_stored_{storage_technology}_MWh") + 1
            temporal_results_bidding_zone.insert(column_index, f"time_stored_{storage_technology}_H", time_stored_H)

        # Store the temporal results to a CSV file
        temporal_results_bidding_zone.to_csv(f"{output_folder}/{resolution}/temporal/{bidding_zone}.csv")

        # Convert and store the production capacity
        production_capacity_bidding_zone = utils.convert_variables_recursively(production_capacity[bidding_zone])
        production_capacity_bidding_zone.to_csv(f"{output_folder}/{resolution}/production/{bidding_zone}.csv")

        # Convert and store the storage capacity
        storage_capacity_bidding_zone = utils.convert_variables_recursively(storage_capacity[bidding_zone])
        storage_capacity_bidding_zone.to_csv(f"{output_folder}/{resolution}/storage/{bidding_zone}.csv")

    # Store the optimization log
    utils.write_text(f"{output_folder}/{resolution}/log.txt", "".join(log_messages))

    # Set the final status
    status.update(f"Optimization has finished and results are stored", type="success")
