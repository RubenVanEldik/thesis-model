import streamlit as st
import optimize
import utils
from datetime import date


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
    return st.sidebar.date_input("Data range", (start_default, end_default), start_data, end_data)


if __name__ == "__main__":
    model_year = st.sidebar.selectbox("Model year", [2025, 2030], index=1)
    countries = select_countries()
    data_range = select_data_range()

    # Run the model if the button has been pressed, otherwise show a message
    if st.sidebar.button("Run model"):
        optimize.run(model_year, countries, data_range)
    else:
        st.info("The model hasnt ran yet.")
