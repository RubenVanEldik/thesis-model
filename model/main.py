from datetime import date
import os
import streamlit as st

import analyze
import optimize
import utils
import validate


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

    def set(self, mode):
        self.mode = mode
        st.experimental_set_query_params(mode=mode)

    def button(self, key, *, label, only_on_click=False):
        button_is_clicked = st.sidebar.button(label, on_click=lambda: mode.set(key))
        has_correct_param = self.get() == key
        return button_is_clicked or (not only_on_click and has_correct_param)


def select_countries():
    """
    Let the user select one or multiple countries to include in the model
    """
    countries = utils.open_yaml("../input/countries.yaml")

    # Let the user select the country
    format_func = lambda code: countries[code]["name"]
    default_countries = ["NL", "BE", "DE"]
    country_codes = st.sidebar.multiselect("Countries", countries.keys(), default=default_countries, format_func=format_func)

    # Return the country object for all selected countries
    return [countries[country_code] for country_code in country_codes]


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


if __name__ == "__main__":
    mode = ModelMode()

    # Settings for a new run
    st.sidebar.title("Run model")
    config = {}
    config["model_year"] = st.sidebar.selectbox("Model year", [2025, 2030], index=1)
    config["countries"] = select_countries()
    config["date_range"] = select_data_range()

    # Run the model if the button has been pressed
    invalid_config = not validate.is_config(config)
    if mode.button("optimization", label="Run model", only_on_click=True):
        optimize.run(config)
        mode.set("analysis")  # Set the mode to analysis so the analysis will automatically run

    # Settings for the analysis
    st.sidebar.title("Analyze previous run")
    previous_runs = sorted(os.listdir("../output"), reverse=True)
    selected_run = st.sidebar.selectbox("Previous runs", previous_runs)

    # Run the analysis if the button has been pressed or the mode is set to analysis
    if mode.button("analysis", label="Analyze run"):
        analyze.run(selected_run)
