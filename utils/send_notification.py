import dotenv
import os
import pushover

import validate


# Load the variables from the .env file
dotenv.load_dotenv(".env")

# Initialize the Pushover client if the keys are available
user_key = os.getenv("PUSHOVER_USER_KEY")
api_token = os.getenv("PUSHOVER_API_TOKEN")
if user_key and api_token:
    client = pushover.Client(user_key, api_token=api_token)


def send_notification(message):
    """
    Send a notification via Pushover, if a key and token are set
    """
    assert validate.is_string(message)

    # Send the message if the client has been intialized
    if "client" in globals():
        client.send_message(message, title="Thesis model")
