from datetime import datetime, timedelta
import gurobipy as gp
import os
import pandas as pd
import re
import streamlit as st

import utils
import validate

from .calculate_time_energy_stored import calculate_time_energy_stored


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
    model = gp.Model(config["name"])
    model.setParam("OutputFlag", 0)
    model.setParam("BarHomogeneous", 1)  # Don't know what this does, but it speeds up some more complex models
    model.setParam("Threads", config["optimization"]["thread_count"])
    model.setParam("Method", config["optimization"]["method"])
    model.setParam("TimeLimit", (config["optimization"]["time_limit"] - datetime.now()).total_seconds())

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
    temporal_export = {}
    production_capacity = {}
    storage_capacity = {}

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
        if not len(temporal_export):
            temporal_export["hvac"] = pd.DataFrame(index=temporal_results[bidding_zone].index)
            temporal_export["hvdc"] = pd.DataFrame(index=temporal_results[bidding_zone].index)

        """
        Step 3B: Define production capacity variables
        """
        temporal_results[bidding_zone]["production_total_MW"] = 0
        for production_technology in config["technologies"]["production"]:
            status.update(f"Adding {utils.labelize_technology(production_technology, capitalize=False)} production to {bidding_zone}")

            # Create a capacity variable for each climate zone
            climate_zones = [re.match(f"{production_technology}_(.+)_cf", column).group(1) for column in temporal_data[bidding_zone].columns if column.startswith(f"{production_technology}_")]
            if previous_resolution:
                previous_production_capacity = utils.read_csv(f"{output_folder}/{previous_resolution}/production/{bidding_zone}.csv", index_col=0)
                capacities = model.addVars(climate_zones, lb=config["time_discretization"]["capacity_propagation"] * previous_production_capacity[production_technology].dropna())
            else:
                capacities = model.addVars(climate_zones)

            # Add the capacities to the production_capacity DataFrame and calculate the temporal production for a specific technology
            temporal_production = 0
            for climate_zone, capacity in capacities.items():
                production_capacity[bidding_zone].loc[climate_zone, production_technology] = capacity
                # Apply is required, otherwise it will throw a ValueError if there are more than a few thousand rows (see https://stackoverflow.com/questions/64801287)
                temporal_production += temporal_data[bidding_zone][f"{production_technology}_{climate_zone}_cf"].apply(lambda cf: cf * capacity)
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
            energy_stored_previous = None
            temporal_energy_stored_dict = {}
            for timestamp in temporal_data[bidding_zone].index:
                status.update(f"Adding {utils.labelize_technology(storage_technology, capitalize=False)} storage to {bidding_zone}", timestamp=timestamp)

                # Create the state of charge variables
                if previous_resolution:
                    energy_stored_current = model.addVar(lb=config["time_discretization"]["soc_propagation"] * previous_temporal_results.loc[timestamp, f"energy_stored_{storage_technology}_MWh"])
                else:
                    energy_stored_current = model.addVar()

                # Add the SOC constraint with regard to the previous timestamp
                if energy_stored_previous:
                    efficiency = assumptions["roundtrip_efficiency"] ** 0.5
                    model.addConstr(energy_stored_current == energy_stored_previous + (inflow[timestamp] * efficiency - outflow[timestamp] / efficiency) * timestep_hours)

                # Add the energy capacity constraints (can't be added when the flow variables are defined because it's a gurobipy.Var)
                model.addConstr(energy_stored_current >= assumptions["soc_min"] * energy_capacity)
                model.addConstr(energy_stored_current <= assumptions["soc_max"] * energy_capacity)

                # Add the power capacity constraints (can't be added when the flow variables are defined because it's a gurobipy.Var)
                model.addConstr(inflow[timestamp] <= power_capacity)
                model.addConstr(outflow[timestamp] <= power_capacity)

                # Add the current energy stored to temporal_energy_stored_dict
                temporal_energy_stored_dict[timestamp] = energy_stored_current

                # Update energy_stored_previous
                energy_stored_previous = energy_stored_current

            # Convert the temporal_energy_stored_dict to a Series
            temporal_energy_stored = pd.Series(data=temporal_energy_stored_dict)

            # Ensure that the SOC of the first timestep equals the SOC of the last timestep
            model.addConstr(temporal_energy_stored.head(1).item() == temporal_energy_stored.tail(1).item())

            # Add the temporal energy stored to the temporal_results DataFrame
            temporal_results[bidding_zone][f"energy_stored_{storage_technology}_MWh"] = temporal_energy_stored
            temporal_results[bidding_zone]["energy_stored_total_MWh"] += temporal_energy_stored

        """
        Step 3D: Define the interconnection variables
        """
        for connection_type in ["hvac", "hvdc"]:
            status.update(f"Adding {connection_type.upper()} interconnections to {bidding_zone}")
            temporal_export_limits = utils.get_export_limits(bidding_zone, type=connection_type, index=temporal_results[bidding_zone].index, config=config)
            for column in temporal_export_limits:
                temporal_export_limit = temporal_export_limits[column] * config["interconnections"]["relative_capacity"]
                temporal_export[connection_type][column] = pd.Series(model.addVars(temporal_export[connection_type].index, ub=temporal_export_limit))

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
        for interconnection_type in temporal_export:
            relevant_temporal_export = [interconnection_bidding_zones for interconnection_bidding_zones in temporal_export[interconnection_type] if bidding_zone in interconnection_bidding_zones]
            for bidding_zone1, bidding_zone2 in relevant_temporal_export:
                direction = 1 if bidding_zone1 == bidding_zone else -config["interconnections"]["efficiency"][interconnection_type]
                other_bidding_zone = bidding_zone1 if bidding_zone2 == bidding_zone else bidding_zone2
                column_name = f"net_export_{other_bidding_zone}_MW"
                if column_name not in temporal_results:
                    temporal_results[bidding_zone][column_name] = 0
                temporal_results[bidding_zone][column_name] += direction * temporal_export[interconnection_type][(bidding_zone1, bidding_zone2)]

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
    Step 5: Define the production potential and self-sufficiency constraints  per country
    """
    for country in config["countries"]:
        status.update(f"Adding production potential and self-sufficiency constraints to {country['name']}")

        # Get the bidding zones for the country
        bidding_zones_in_country = utils.get_bidding_zones_for_countries([country["nuts_2"]])

        # Add a production capacity constraint per production technology per country
        for production_technology in config["technologies"]["production"]:
            # Don't add a constraint if the production technology has no potential specified for this country
            if not production_technology in country["potential"]:
                continue

            # Add a constraint so cumulative production capacity in the country is always smaller than the potential for that technology
            total_production_capacity = sum(production_capacity[bidding_zone][production_technology].sum() for bidding_zone in bidding_zones_in_country)
            model.addConstr(total_production_capacity <= country["potential"][production_technology])

        # Add a self-sufficiency constraint for each year
        for year in temporal_results[bidding_zone].index.year.unique():
            total_demand = 0
            total_production = 0

            # Sum the demand and production for all bidding zones
            for bidding_zone in bidding_zones_in_country:
                annual_temporal_results_bidding_zone = temporal_results[bidding_zone][temporal_results[bidding_zone].index.year == year]

                # Calculate the total demand and non-curtailed production in this country
                total_demand += annual_temporal_results_bidding_zone.demand_MW.sum()
                total_production += (annual_temporal_results_bidding_zone.production_total_MW - annual_temporal_results_bidding_zone.curtailed_MW).sum()

            # Add a constraint so cumulative production over the cumulative demand is always greater than the minimum self-sufficiency factor
            min_self_sufficiency = config["interconnections"]["min_self_sufficiency"]
            model.addConstr(total_production / total_demand >= min_self_sufficiency)

    """
    Step 6: Set objective function
    """
    temporal_demand = utils.merge_dataframes_on_column(temporal_results, "demand_MW")
    firm_lcoe = utils.calculate_lcoe(production_capacity, storage_capacity, temporal_demand, config=config)
    model.setObjective(firm_lcoe, gp.GRB.MINIMIZE)

    """
    Step 7: Solve model
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

    # Store the optimization log
    os.makedirs(f"{output_folder}/{resolution}")
    utils.write_text(f"{output_folder}/{resolution}/log.txt", "".join(log_messages))

    """
    Step 8: Check if the model could be solved
    """
    if model.status == gp.GRB.INFEASIBLE:
        return "The model was infeasible"
    if model.status == gp.GRB.UNBOUNDED:
        return "The model was unbounded"
    if model.status == gp.GRB.INF_OR_UNBD:
        return "The model was either infeasible or unbounded"
    if model.status == gp.GRB.CUTOFF:
        return "The optimal objective for the model was worse than the value specified in the Cutoff parameter"
    if model.status == gp.GRB.ITERATION_LIMIT:
        return "The optimization terminated because the total number of iterations performed exceeded the value specified in the IterationLimit or BarIterLimit parameter"
    if model.status == gp.GRB.NODE_LIMIT:
        return "The optimization terminated because the total number of branch-and-cut nodes explored exceeded the value specified in the NodeLimit parameter"
    if model.status == gp.GRB.TIME_LIMIT:
        return f"The optimization terminated due to the time limit in {timedelta(seconds=model.Runtime)}"
    if model.status == gp.GRB.SOLUTION_LIMIT:
        return "The optimization terminated because the number of solutions found reached the value specified in the SolutionLimit parameter"
    if model.status == gp.GRB.INTERRUPTED:
        return "The optimization was terminated by the user"
    if model.status == gp.GRB.NUMERIC:
        return "The optimization was terminated due to unrecoverable numerical difficulties"
    if model.status == gp.GRB.SUBOPTIMAL:
        return "Unable to satisfy optimality tolerances; a sub-optimal solution is available"
    if model.status != gp.GRB.OPTIMAL:
        return "The model could for an unknown reason not be solved"

    """
    Step 9: Store the results
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
