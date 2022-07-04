import utils
import validate


def is_last_resolution(resolution, *, config):
    """
    Check if the given resolution is the last one in the config
    """
    assert validate.is_resolution(resolution)
    assert validate.is_config(config)

    # Get
    last_resolution = utils.get_sorted_resolution_stages(config, descending=True)[-1]

    return resolution == last_resolution
