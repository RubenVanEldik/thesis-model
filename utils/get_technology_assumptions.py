import utils
import validate


def get_technology_assumptions(type, technology, *, scenario):
    """
    Return the assumptions dictionary for a specific technology
    """
    assert validate.is_technology_type(type)
    assert validate.is_technology(technology)
    assert validate.is_technology_scenario(scenario)

    # Import the assumptions
    assumptions = utils.read_yaml(utils.path("input", "technologies", f"{type}.yaml"))
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
