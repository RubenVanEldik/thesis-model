import os

import validate


def _validate_run(run_name):
    """
    Check if the run has been completed
    """
    assert validate.is_string(run_name)

    # Return True if it has a config.yaml file
    if os.path.isfile(f"./output/{run_name}/config.yaml"):
        return True

    # Return True if it has a sensitivity.yaml file
    if os.path.isfile(f"./output/{run_name}/sensitivity.yaml"):
        return True

    # Return False if has neither a config.yaml or sensitivity.yaml file
    return False


def get_previous_runs(*, include_uncompleted_runs=False):
    """
    Get a list with the names of all previous runs
    """
    assert validate.is_bool(include_uncompleted_runs)

    output_folder = "./output"

    # Return an empty list if there is no output folder
    if not os.path.isdir(output_folder):
        return []

    files_and_directories = os.listdir(output_folder)
    directories = [item for item in files_and_directories if os.path.isdir(os.path.join(output_folder, item))]
    directories = sorted(directories, reverse=True)

    # Return a list of all runs
    if include_uncompleted_runs:
        return directories

    # Return a list of all completed runs
    return [item for item in directories if _validate_run(item)]
