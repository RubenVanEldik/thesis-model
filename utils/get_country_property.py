import utils
import validate


def get_country_property(country_code, key, *, type="nuts_2"):
    """
    Get a specific property of a country via its code
    """
    assert validate.is_country_code_type(type)
    assert validate.is_country_code(country_code, type=type)
    assert validate.is_string(key)

    # Read the countries
    countries = utils.read_yaml("./input/countries.yaml")

    # Get the specific country
    country = next(country for country in countries if country[type] == country_code)

    # Return the key from the country
    return country.get(key)
