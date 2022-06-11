from datetime import date, datetime, time, timedelta
import numpy as np
import os
import re
import streamlit as st

import optimize
import utils
import validate


def get_default_name():
    runs = utils.get_previous_runs()
    runs_with_proper_names = [run for run in runs if re.search(r"^run_\d\d\d\d", run)]

    # Calculate what the next default name should be
    if runs_with_proper_names:
        last_run_with_proper_name = runs_with_proper_names[0]
        last_run_number = re.search(r"^run_(\d\d\d\d)", last_run_with_proper_name).group(1)
        default_name = f"run_{int(last_run_number) + 1:04}"
    else:
        default_name = "run_0001"
    return default_name


# Settings dictionary for the new run
config = {}

# Ask for the name of the this run
config["name"] = st.sidebar.text_input("Name", value=get_default_name(), max_chars=50)

# Set the scope options
with st.sidebar.expander("Scope"):
    # Select the model year
    config["model_year"] = st.selectbox("Model year", [2025, 2030], index=1)

    # Select the countries
    countries = utils.read_yaml("./input/countries.yaml")
    country_codes = [country["nuts_2"] for country in countries]
    default_countries = ["NL", "BE", "DE"]
    format_func = lambda nuts_2: next((country["name"] for country in countries if country["nuts_2"] == nuts_2), None)
    selected_countries = st.multiselect("Countries", country_codes, default=default_countries, format_func=format_func)
    config["countries"] = [country for country in countries if country["nuts_2"] in selected_countries]

    # Select the date range
    start_default = date(2016, 1, 1)
    end_default = date(2016, 12, 31)
    start_data = date(1982, 1, 1)
    end_data = date(2016, 12, 31)
    date_range = st.date_input("Climate data range", (start_default, end_default), start_data, end_data)
    if len(date_range) == 2:
        config["date_range"] = {"start": date_range[0], "end": date_range[1]}

# Set the technology options
with st.sidebar.expander("Technologies"):
    config["technologies"] = {}

    # Select the scenario
    scenario = st.select_slider("Scenario", options=["conservative", "moderate", "advanced"], value="moderate", format_func=utils.format_str)
    config["technologies"]["scenario"] = scenario

    # Select the production technologies
    col1, col2 = st.columns(2)
    col1.subheader("Production")
    config["technologies"]["production"] = {}
    production_technology_options = utils.read_yaml("./input/technologies/production.yaml").keys()
    for technology in production_technology_options:
        if col1.checkbox(utils.labelize_technology(technology), value=True):
            config["technologies"]["production"][technology] = utils.get_technology_assumptions("production", technology, scenario=scenario)

    # Select the storage technologies
    col2.subheader("Storage")
    config["technologies"]["storage"] = {}
    storage_technologies_options = utils.read_yaml("./input/technologies/storage.yaml").keys()
    for technology in storage_technologies_options:
        if col2.checkbox(utils.labelize_technology(technology), value=True):
            config["technologies"]["storage"][technology] = utils.get_technology_assumptions("storage", technology, scenario=scenario)

# Set the interconnection options
with st.sidebar.expander("Interconnections"):
    config["interconnections"] = {"efficiency": {}}
    config["interconnections"]["relative_capacity"] = st.slider("Relative capacity", value=1.0, max_value=1.5, step=0.05)
    config["interconnections"]["efficiency"]["hvac"] = st.number_input("Efficiency HVAC", value=0.95, max_value=1.0)
    config["interconnections"]["efficiency"]["hvdc"] = st.number_input("Efficiency HVDC", value=0.95, max_value=1.0)

# Set the sensitivity analysis options
with st.sidebar.expander("Sensitivity analysis"):
    sensitivity_config = {}

    # Enable/disable the sensitivity analysis
    sensitivity_enabled = st.checkbox("Enabled")

    # Create a dictionary with the sensitivity options
    sensitivity_options = {}
    sensitivity_options["interconnections.relative_capacity"] = "Interconnection capacity"
    sensitivity_options["interconnections.efficiency.hvac"] = "HVAC efficiency"
    sensitivity_options["interconnections.efficiency.hvdc"] = "HVDC efficiency"
    for production_technology in config["technologies"]["production"]:
        production_technology_label = utils.labelize_technology(production_technology)
        sensitivity_options[f"technologies.production.{production_technology}.economic_lifetime"] = f"{production_technology_label} - Economic lifetime"
        sensitivity_options[f"technologies.production.{production_technology}.capex"] = f"{production_technology_label} - CAPEX"
        sensitivity_options[f"technologies.production.{production_technology}.fixed_om"] = f"{production_technology_label} - Fixed O&M"
        sensitivity_options[f"technologies.production.{production_technology}.variable_om"] = f"{production_technology_label} - Variable O&M"
        sensitivity_options[f"technologies.production.{production_technology}.wacc"] = f"{production_technology_label} - WACC"
    for storage_technology in config["technologies"]["storage"]:
        storage_technology_label = utils.labelize_technology(storage_technology)
        sensitivity_options[f"technologies.storage.{storage_technology}.economic_lifetime"] = f"{storage_technology_label} - Economic lifetime"
        sensitivity_options[f"technologies.storage.{storage_technology}.energy_capex"] = f"{storage_technology_label} - Energy CAPEX"
        sensitivity_options[f"technologies.storage.{storage_technology}.power_capex"] = f"{storage_technology_label} - Power CAPEX"
        sensitivity_options[f"technologies.storage.{storage_technology}.fixed_om"] = f"{storage_technology_label} - Fixed O&M"
        sensitivity_options[f"technologies.storage.{storage_technology}.roundtrip_efficiency"] = f"{storage_technology_label} - Roundtrip efficiency"
        sensitivity_options[f"technologies.storage.{storage_technology}.wacc"] = f"{storage_technology_label} - WACC"

    # Select the sensitivity variables
    sensitivity_config["variables"] = st.multiselect("Variables", sensitivity_options.keys(), format_func=lambda key: sensitivity_options[key], disabled=not sensitivity_enabled)

    # Select the sensitivity range and steps
    sensitivity_start, sensitivity_stop = st.slider("Relative range", value=(0.5, 1.5), min_value=0.0, max_value=2.0, step=0.05, disabled=not sensitivity_enabled)
    number_steps = st.slider("Number of steps", value=5, min_value=3, max_value=15, step=2, disabled=not sensitivity_enabled)
    sensitity_steps = np.linspace(start=sensitivity_start, stop=sensitivity_stop, num=number_steps)
    sensitivity_config["steps"] = dict([(f"{step:.3f}", float(step)) for step in sensitity_steps])

# Set the optimization parameters
with st.sidebar.expander("Optimization parameters"):
    config["optimization"] = {}

    # Select the resolution steps
    resolutions = ["1H", "2H", "4H", "6H", "12H", "1D", "2D", "1W"]
    config["resolution_stages"] = st.multiselect("Resolution stages", resolutions, default=["1H"], format_func=utils.format_resolution)

    # Select the optimization method
    method_options = {-1: "Automatic", 0: "Primal simplex", 1: "Dual simplex", 2: "Barrier", 3: "Concurrent", 4: "Deterministic concurrent", 5: "Deterministic concurrent simplex"}
    config["optimization"]["method"] = st.selectbox("Method", method_options.keys(), format_func=lambda key: method_options[key])

    # Select the time limit
    col1, col2 = st.columns(2)
    end_date = col1.date_input("End date", value=datetime.now() + timedelta(days=1), min_value=datetime.now())
    end_time = col2.time_input("End time", value=time(9))
    config["optimization"]["time_limit"] = datetime.combine(end_date, end_time)

    # Select the thread count
    cpu_count = os.cpu_count()
    config["optimization"]["thread_count"] = st.slider("Thread count", value=cpu_count, min_value=1, max_value=cpu_count)


# Run the model if the button has been pressed
invalid_config = not validate.is_config(config, new_config=True)
invalid_sensitivity_config = sensitivity_enabled and not validate.is_sensitivity_config(sensitivity_config)
if st.sidebar.button("Run model", disabled=invalid_config or invalid_sensitivity_config):
    if config["name"] in utils.get_previous_runs():
        st.error(f"There is already a run called '{config['name']}'")
    elif sensitivity_enabled:
        optimize.run_sensitivity(config, sensitivity_config)
    else:
        optimize.run(config, output_folder=f"./output/{config['name']}")
