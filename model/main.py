from datetime import datetime, time, date, timedelta
import numpy as np
import os
import streamlit as st

import analyze
import optimize
import technologies
import utils
import validate
import re


class ModelMode:
    mode = None

    def __init__(self):
        # Set the page config
        menu_items = {"Get Help": None, "Report a bug": None, "About": None}
        st.set_page_config(page_title="Thesis model", page_icon="🌤️", menu_items=menu_items)

        # Get the mode
        self.mode = self.get()

    def get(self):
        params = st.experimental_get_query_params()
        self.mode = params["mode"][0] if params.get("mode") else None
        return self.mode

    def set(self, mode=None):
        if mode:
            self.mode = mode
            st.experimental_set_query_params(mode=mode)
        else:
            st.experimental_set_query_params()

    def button(self, key, *, label, only_on_click=False, disabled=False):
        button_is_clicked = st.sidebar.button(label, on_click=lambda: mode.set(key), disabled=disabled)
        has_correct_param = self.get() == key
        return button_is_clicked or (not only_on_click and has_correct_param)


def get_previous_runs():
    """
    Get the names of all previous runs
    """
    output_folder = "../output"
    files_and_directories = os.listdir(output_folder)
    directories = [item for item in files_and_directories if os.path.isdir(os.path.join(output_folder, item))]
    return sorted(directories, reverse=True)


def select_name():
    """
    Let the user create a name for this run
    """
    runs = get_previous_runs()
    runs_with_proper_names = [run for run in runs if re.search(r"^Run \d\d\d\d", run)]

    # Calculate what the next default name should be
    if runs_with_proper_names:
        last_run_with_proper_name = runs_with_proper_names[0]
        last_run_number = re.search(r"^Run (\d\d\d\d)", last_run_with_proper_name).group(1)
        default_name = f"Run {int(last_run_number) + 1:04}"
    else:
        default_name = "Run 0001"

    # Return the name for the next run
    return st.sidebar.text_input("Name", value=default_name, max_chars=50)


def select_countries():
    """
    Let the user select one or multiple countries to include in the model
    """
    countries = utils.open_yaml(os.path.join("../input", "countries.yaml"))

    # Let the user select the country
    country_codes = [country["code"] for country in countries]
    default_countries = ["NL", "BE", "DE"]
    format_func = lambda code: next((country["name"] for country in countries if country["code"] == code), None)
    selected_countries = st.multiselect("Countries", country_codes, default=default_countries, format_func=format_func)

    # Return the country object for all selected countries
    return [country for country in countries if country["code"] in selected_countries]


def select_data_range():
    """
    Let the user select the range of demand/climate data that will be used
    """
    start_default = date(2016, 1, 1)
    end_default = date(2016, 12, 31)
    start_data = date(1982, 1, 1)
    end_data = date(2016, 12, 31)
    date_range = st.date_input("Climate data range", (start_default, end_default), start_data, end_data)

    if len(date_range) != 2:
        return None

    return {"start": date_range[0], "end": date_range[1]}


def select_technologies(scenario):
    col1, col2 = st.columns(2)

    # Add the checked production technologies
    col1.subheader("Production")
    production_technologies = {}
    for technology in technologies.technology_types("production"):
        if col1.checkbox(technologies.labelize(technology), value=True):
            production_technologies[technology] = technologies.assumptions("production", technology, scenario=scenario)

    # Add the checked storagetechnologies
    col2.subheader("Storage")
    storage_technologies = {}
    for technology in technologies.technology_types("storage"):
        if col2.checkbox(technologies.labelize(technology), value=True):
            storage_technologies[technology] = technologies.assumptions("storage", technology, scenario=scenario)

    # Return the checked production and storage technologies
    return {"production": production_technologies, "storage": storage_technologies}


def get_sensitivity_options(config):
    options = {}
    options["interconnections.relative_capacity"] = "Interconnection capacity"
    options["interconnections.efficiency.hvac"] = "HVAC efficiency"
    options["interconnections.efficiency.hvdc"] = "HVDC efficiency"
    for production_technology in config["technologies"]["production"]:
        production_technology_label = technologies.labelize(production_technology)
        options[f"technologies.production.{production_technology}.economic_lifetime"] = f"{production_technology_label} - Economic lifetime"
        options[f"technologies.production.{production_technology}.capex"] = f"{production_technology_label} - CAPEX"
        options[f"technologies.production.{production_technology}.fixed_om"] = f"{production_technology_label} - Fixed O&M"
        options[f"technologies.production.{production_technology}.variable_om"] = f"{production_technology_label} - Variable O&M"
        options[f"technologies.production.{production_technology}.wacc"] = f"{production_technology_label} - WACC"
    for storage_technology in config["technologies"]["storage"]:
        storage_technology_label = technologies.labelize(storage_technology)
        options[f"technologies.storage.{storage_technology}.economic_lifetime"] = f"{storage_technology_label} - Economic lifetime"
        options[f"technologies.storage.{storage_technology}.energy_capex"] = f"{storage_technology_label} - Energy CAPEX"
        options[f"technologies.storage.{storage_technology}.power_capex"] = f"{storage_technology_label} - Power CAPEX"
        options[f"technologies.storage.{storage_technology}.fixed_om"] = f"{storage_technology_label} - Fixed O&M"
        options[f"technologies.storage.{storage_technology}.roundtrip_efficiency"] = f"{storage_technology_label} - Roundtrip efficiency"
        options[f"technologies.storage.{storage_technology}.wacc"] = f"{storage_technology_label} - WACC"
    return options


def select_time_limit():
    col1, col2 = st.columns(2)
    end_date = col1.date_input("End date", value=datetime.now() + timedelta(days=1), min_value=datetime.now())
    end_time = col2.time_input("End time", value=time(9))
    return datetime.combine(end_date, end_time)


def select_method():
    method_options = {-1: "Automatic", 0: "Primal simplex", 1: "Dual simplex", 2: "Barrier", 3: "Concurrent", 4: "Deterministic concurrent", 5: "Deterministic concurrent simplex"}
    return st.selectbox("Method", method_options.keys(), format_func=lambda key: method_options[key])


def select_thread_count():
    cpu_count = os.cpu_count()
    return st.slider("Thread count", value=cpu_count, min_value=1, max_value=cpu_count)


if __name__ == "__main__":
    mode = ModelMode()
    st.sidebar.image("./logo.png", width=None)

    # Settings for a new run
    st.sidebar.title("Run model")
    config = {}
    config["name"] = select_name()
    with st.sidebar.expander("Scope"):
        config["model_year"] = st.selectbox("Model year", [2025, 2030], index=1)
        config["countries"] = select_countries()
        config["date_range"] = select_data_range()
    with st.sidebar.expander("Technologies"):
        config["technologies"] = {}
        scenario = st.select_slider("Scenario", options=["conservative", "moderate", "advanced"], value="moderate", format_func=lambda option: option.capitalize())
        config["technologies"]["scenario"] = scenario
        config["technologies"] = select_technologies(scenario)
    with st.sidebar.expander("Interconnections"):
        config["interconnections"] = {"efficiency": {}}
        config["interconnections"]["relative_capacity"] = st.slider("Relative capacity", value=1.0, max_value=1.5, step=0.05)
        config["interconnections"]["efficiency"]["hvac"] = st.number_input("Efficiency HVAC", value=0.95, max_value=1.0)
        config["interconnections"]["efficiency"]["hvdc"] = st.number_input("Efficiency HVDC", value=0.95, max_value=1.0)
    with st.sidebar.expander("Sensitivity analysis"):
        # Toggle the sensitivity analysis
        sensitivity_enabled = st.checkbox("Enabled")
        sensitivity_config = {}

        # Select the sensitivity variables
        sensitivity_options = get_sensitivity_options(config)
        sensitivity_config["variables"] = st.multiselect("Variables", sensitivity_options.keys(), format_func=lambda key: sensitivity_options[key], disabled=not sensitivity_enabled)

        # Select the sensitivity range and steps
        sensitivity_start, sensitivity_stop = st.slider("Relative range", value=(0.5, 1.5), min_value=0.0, max_value=2.0, step=0.05, disabled=not sensitivity_enabled)
        number_steps = st.slider("Number of steps", value=5, min_value=3, max_value=15, step=2, disabled=not sensitivity_enabled)
        sensitity_steps = np.linspace(start=sensitivity_start, stop=sensitivity_stop, num=number_steps)
        sensitivity_config["steps"] = dict([(f"{step:.3f}", float(step)) for step in sensitity_steps])
    with st.sidebar.expander("Optimization parameters"):
        config["optimization"] = {}
        config["optimization"]["method"] = select_method()
        config["optimization"]["time_limit"] = select_time_limit()
        config["optimization"]["thread_count"] = select_thread_count()

    # Run the model if the button has been pressed
    invalid_config = not validate.is_config(config)
    invalid_sensitivity_config = sensitivity_enabled and not validate.is_sensitivity_config(sensitivity_config)
    if mode.button("optimization", label="Run model", only_on_click=True, disabled=invalid_config or invalid_sensitivity_config):
        if config["name"] in get_previous_runs():
            st.error(f"There is already a run called '{config['name']}'")
        elif sensitivity_enabled:
            optimize.run_sensitivity(config, sensitivity_config)
        else:
            optimize.run(config, output_folder=f"../output/{config['name']}")
        mode.set(None)  # Set the mode to None so the URL params are updated

    # Settings for the analysis
    st.sidebar.title("Analyze previous run")
    previous_runs = get_previous_runs()
    selected_run = st.sidebar.selectbox("Previous runs", previous_runs)
    if os.path.isfile(f"../output/{selected_run}/sensitivity.yaml"):
        analysis = "sensitivity"
    else:
        analysis_options = ["statistics", "hourly_results", "duration_curve"]
        analysis = st.sidebar.selectbox("Analyses", analysis_options, format_func=lambda option: option.replace("_", " ").capitalize())

    # Run the analysis if the button has been pressed or the mode is set to analysis
    if mode.button("analysis", label="Analyze run", disabled=not selected_run):
        getattr(analyze, analysis)(selected_run)
