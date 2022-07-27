import validate


def format_technology(key, *, capitalize=True):
    """
    Format the name of a specific technology
    """
    assert validate.is_technology(key)
    assert validate.is_bool(capitalize)

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
