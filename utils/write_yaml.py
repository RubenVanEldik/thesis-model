import yaml

import validate


def write_yaml(filepath, data, *, allow_overwrite=False):
    """
    Store a dictionary or list as .yaml file
    """
    assert validate.is_filepath(filepath, suffix=".yaml", existing=None if allow_overwrite else False)
    assert validate.is_dict_or_list(data)
    assert validate.is_bool(allow_overwrite)

    # Read and parse the file
    with open(filepath, "w") as f:
        return yaml.dump(data, f, Dumper=yaml.Dumper)
