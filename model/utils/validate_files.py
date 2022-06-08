import os

import validate


def validate_files(filenames):
    """
    Check if all all files in a list exist
    """
    assert validate.is_filepath_list(filenames)

    return all(os.path.isfile(filename) for filename in filenames)
