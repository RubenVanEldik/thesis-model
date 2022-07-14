import re

import utils


def get_next_run_name():
    """
    Return a string with the new run name
    """
    # Get all runs
    runs = utils.get_previous_runs(include_uncompleted_runs=True)
    runs_with_proper_names = [run for run in runs if re.search(r"^Run \d\d\d\d", run)]

    # Return 'Run 0001' if there are no previous runs
    if not runs_with_proper_names:
        return "Run 0001"

    # Return the next run name
    last_run_with_proper_name = runs_with_proper_names[0]
    last_run_number = re.search(r"^Run (\d\d\d\d)", last_run_with_proper_name).group(1)
    return f"Run {int(last_run_number) + 1:04}"
