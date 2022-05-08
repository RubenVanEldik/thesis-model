import pandas as pd
import streamlit as st

import utils
import validate


def technology_types(type):
    """
    Return a list of all technology types
    """
    assert validate.is_technology_type(type)

    # Import the assumptions
    assumptions = utils.read_yaml(f"../input/technologies/{type}.yaml")

    # Return the keys of all technologies
    return assumptions.keys()


def assumptions(type, technology, *, scenario):
    """
    Return the assumptions dictionary for a specific technology
    """
    assert validate.is_technology_type(type)
    assert validate.is_technology(technology)
    assert validate.is_technology_scenario(scenario)

    # Import the assumptions
    assumptions = utils.read_yaml(f"../input/technologies/{type}.yaml")
    assumptions = assumptions[technology]

    # Merge the general and scenario specific assumptions
    assumptions_scenario = {}
    for key, value in assumptions.items():
        if key == scenario:
            assumptions_scenario = {**assumptions_scenario, **assumptions[key]}
        elif not validate.is_technology_scenario(key):
            assumptions_scenario[key] = value

    # Calculate and add the economic capital recovery factor (crf)
    if all(key in assumptions_scenario.keys() for key in ["wacc", "economic_lifetime"]):
        wacc = assumptions_scenario["wacc"]
        economic_lifetime = assumptions_scenario["economic_lifetime"]
        assumptions_scenario["crf"] = wacc / (1 - (1 + wacc) ** (-economic_lifetime))

    # Return the assumptions for a specific scenario
    return assumptions_scenario


def labelize(key, *, capitalize=True):
    """
    Return the label for a specific technology key
    """
    assert validate.is_technology(key)

    if key == "pv":
        label = "solar PV"
    if key == "onshore":
        label = "onshore wind"
    if key == "offshore":
        label = "offshore wind"
    if key == "lion":
        label = "Li-ion"
    if key == "hydrogen":
        label = "hydrogen"

    return (label[0].upper() + label[1:]) if capitalize else label
