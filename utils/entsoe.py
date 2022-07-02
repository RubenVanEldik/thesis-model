import dotenv
from entsoe import EntsoePandasClient
import os

# Load the variables from the .env file
api_key = os.getenv("ENTSOE_KEY")

# Raise an error if the API key has not been set
dotenv.load_dotenv(".env")
if not api_key:
    raise KeyError("ENTSOE_KEY variable has not been set")

# Return an initialized ENTSO-E Pandas client
entsoe = EntsoePandasClient(api_key=api_key)
