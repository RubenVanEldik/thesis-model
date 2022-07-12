import yaml

import validate


def write_yaml(filepath, data):
    """
    Store a dictionary or list as .yaml file
    """
    assert validate.is_filepath(filepath, suffix=".yaml", existing=False)
    assert validate.is_dict_or_list(data)

    # Read and parse the file
    with open(filepath, "w") as f:
        return yaml.dump(data, f, Dumper=yaml.Dumper)
