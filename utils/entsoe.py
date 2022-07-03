import dotenv
from entsoe import EntsoePandasClient
import os

# Load the variables from the .env file
dotenv.load_dotenv(".env")

# Raise an error if the API key has not been set
api_key = os.getenv("ENTSOE_KEY")
if not api_key:
    raise KeyError("ENTSOE_KEY variable has not been set")

# Return an initialized ENTSO-E Pandas client
entsoe = EntsoePandasClient(api_key=api_key)
