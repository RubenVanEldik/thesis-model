import pandas as pd
import streamlit as st
import utils


def assumptions(type, technology, *, scenario="moderate"):
    """
    Return the assumptions dictionary for a specific technology
    """
    # Validate the input
    scenarios = ["conservative", "moderate", "advanced"]
    assert type == "production" or type == "storage"
    assert scenario in scenarios

    # Import the assumptions
    assumptions = utils.open_yaml(f"../input/technologies/{type}.yaml")
    assumptions = assumptions[technology]

    # Merge the general and scenario specific assumptions
    assumptions_scenario = {}
    for key, value in assumptions.items():
        if key in scenarios:
            assumptions_scenario = {**assumptions_scenario, **assumptions[key]}
        else:
            assumptions_scenario[key] = value

    # Calculate and add the economic capital recovery factor (crf)
    if all(key in assumptions_scenario.values() for key in ["wacc", "economic_lifetime"]):
        wacc = assumptions_scenario["wacc"]
        economic_lifetime = assumptions_scenario["economic_lifetime"]
        assumptions_scenario["crf"] = wacc / (1 - (1 + wacc) ^ (-economic_lifetime))

    # Return the assumptions for a specific scenario
    return assumptions_scenario
