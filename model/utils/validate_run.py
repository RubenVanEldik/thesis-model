import os

import validate


def validate_run(run_name):
    """
    Check if the run has been completed
    """
    assert validate.is_string(run_name)

    # Return True if it has a config.yaml file
    if os.path.isfile(f"./output/{run_name}/config.yaml"):
        return True

    # Return True if it has a sensitivity.yaml file
    if os.path.isfile(f"./output/{run_name}/sensitivity.yaml"):
        return True

    # Return False if has neither a config.yaml or sensitivity.yaml file
    return False
