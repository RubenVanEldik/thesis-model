import dotenv
import os

import validate


# Load the variables from the .env file
dotenv.load_dotenv(".env")


def getenv(env_name, *, required=True):
    """
    Get the value for a specific environment variable
    """
    assert validate.is_string(env_name)
    assert validate.is_bool(required)

    # Get the environment variable
    env_value = os.getenv(env_name)

    # Return an error if the environment variable is required and missing
    if required:
        assert env_value is not None

    # Return the environment variable
    return env_value
