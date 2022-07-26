from entsoe import EntsoePandasClient

from .getenv import getenv


# Raise an error if the API key has not been set
api_key = getenv("ENTSOE_KEY")
if not api_key:
    raise KeyError("ENTSOE_KEY variable has not been set")

# Initialize the entsoe_client
entsoe_client = EntsoePandasClient(api_key=api_key)
