import dotenv
from entsoe import EntsoePandasClient
import os

# Load the variables from the .env file
dotenv.load_dotenv(".env")


def entsoe_client():
    # Raise an error if the API key has not been set
    api_key = os.getenv("ENTSOE_KEY")
    if not api_key:
        raise KeyError("ENTSOE_KEY variable has not been set")

    return EntsoePandasClient(api_key=api_key)
