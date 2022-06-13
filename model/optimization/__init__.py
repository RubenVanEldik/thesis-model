from copy import deepcopy
import pandas as pd
import streamlit as st

import utils
import validate

from .optimize import optimize
from .status import Status


def run(config, *, status=Status(), output_folder):
    previous_output_folder = None

    sorted_resolution_stages = sorted(config["resolution_stages"], key=lambda resolution: pd.Timedelta(resolution).total_seconds(), reverse=True)
    for resolution in sorted_resolution_stages:
        full_output_folder = f"{output_folder}/{resolution}"
        optimize(config, resolution=resolution, status=status, output_folder=full_output_folder, previous_output_folder=previous_output_folder)
        previous_output_folder = full_output_folder


def run_sensitivity(config, sensitivity_config):
    """
    Run the model for each step in the sensitivity analysis
    """
    assert validate.is_config(config, new_config=True)
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
