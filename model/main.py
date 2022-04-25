from datetime import datetime, date, timedelta
import os
import streamlit as st

import analyze
import optimize
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
    selected_countries = st.sidebar.multiselect("Countries", country_codes, default=default_countries, format_func=format_func)

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
    date_range = st.sidebar.date_input("Climate data range", (start_default, end_default), start_data, end_data)

    if len(date_range) != 2:
        return None

    return {"start": date_range[0], "end": date_range[1]}


def select_time_limit():
    col1, col2 = st.columns(2)
    end_date = col1.date_input("End date", min_value=datetime.now())
    end_time = col2.time_input("End time", value=datetime.now() + timedelta(hours=1))
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
    config["model_year"] = st.sidebar.selectbox("Model year", [2025, 2030], index=1)
    config["countries"] = select_countries()
    config["date_range"] = select_data_range()
    with st.sidebar.expander("Optimization parameters"):
        config["optimization_method"] = select_method()
        config["optimization_time_limit"] = select_time_limit()
        config["thread_count"] = select_thread_count()

    # Run the model if the button has been pressed
    invalid_config = not validate.is_config(config)
    if mode.button("optimization", label="Run model", only_on_click=True, disabled=invalid_config):
        if config["name"] in get_previous_runs():
            st.error(f"There is already a run called '{config['name']}'")
        else:
            optimize.run(config)
        mode.set(None)  # Set the mode to None so the URL params are updated

    # Settings for the analysis
    st.sidebar.title("Analyze previous run")
    previous_runs = get_previous_runs()
    selected_run = st.sidebar.selectbox("Previous runs", previous_runs)
    analysis_options = ["statistics", "hourly_results", "duration_curve"]
    analysis = st.sidebar.selectbox("Analyses", analysis_options, format_func=lambda option: option.replace("_", " ").capitalize())

    # Run the analysis if the button has been pressed or the mode is set to analysis
    if mode.button("analysis", label="Analyze run", disabled=not selected_run):
        getattr(analyze, analysis)(selected_run)
