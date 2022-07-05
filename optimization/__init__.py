from copy import deepcopy
import pandas as pd
import streamlit as st

import utils
import validate

from .optimize import optimize
from .status import Status


def run(config, *, status=Status(), output_folder):
    previous_resolution = None

    for resolution in utils.get_sorted_resolution_stages(config, descending=True):
        error_message = optimize(config, resolution=resolution, previous_resolution=previous_resolution, status=status, output_folder=output_folder)

        # Stop the run if an error occured during the optimization of one of the resolutions
        if error_message:
            status.update(error_message, type="error")
            return

        previous_resolution = resolution

    # Store the config as a .YAML file
    utils.write_yaml(f"{output_folder}/config.yaml", config)

    # Set the final status
    status.update(f"Optimization has finished and results are stored", type="success")


def run_sensitivity(config, sensitivity_config):
    """
    Run the model for each step in the sensitivity analysis
    """
    assert validate.is_config(config)
    assert validate.is_sensitivity_config(sensitivity_config)

    status = Status()
    output_folder = f"./output/{config['name']}"

    # Loop over each sensitivity analysis step
    for step_key, step_value in sensitivity_config["steps"].items():
        st.subheader(f"Sensitivity run {list(sensitivity_config['steps'].keys()).index(step_key) + 1}/{len(sensitivity_config['steps'])}")
        step_config = deepcopy(config)

        # Update each config variable that is part of the sensitivity analysis
        for variable_key in sensitivity_config["variables"]:
            variable_value = utils.get_nested_key(step_config, variable_key)
            utils.set_nested_key(step_config, variable_key, variable_value * step_value)

        # Run the optimization
        run(step_config, status=status, output_folder=f"{output_folder}/{step_key}")

    # Store the sensitivity config file
    utils.write_yaml(f"{output_folder}/sensitivity.yaml", sensitivity_config)

    # Set the final status
    status.update(f"Sensitivity analysis has finished and results are stored", type="success")
