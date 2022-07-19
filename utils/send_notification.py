import pushover

import utils
import validate


# Initialize the Pushover client if the keys are available
user_key = utils.getenv("PUSHOVER_USER_KEY", required=False)
api_token = utils.getenv("PUSHOVER_API_TOKEN", required=False)
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
