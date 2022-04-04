from datetime import date
import streamlit as st

import optimize
import utils
import validate


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
    # Set the page config
    menu_items = {"Get Help": None, "Report a bug": None, "About": None}
    st.set_page_config(page_title="Thesis model", page_icon="🌤️", menu_items=menu_items)

    # Collect the model config parameters
    config = {}
    config["model_year"] = st.sidebar.selectbox("Model year", [2025, 2030], index=1)
    config["countries"] = select_countries()
    config["date_range"] = select_data_range()

    # Run the model if the button has been pressed
    invalid_config = not validate.is_config(config)
    if st.sidebar.button("Run model", disabled=invalid_config):
        optimize.run(config)
