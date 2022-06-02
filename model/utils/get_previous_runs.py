import os


def get_previous_runs():
    """
    Get the names of all previous runs
    """
    output_folder = "./output"
    files_and_directories = os.listdir(output_folder)
    directories = [item for item in files_and_directories if os.path.isdir(os.path.join(output_folder, item))]
    return sorted(directories, reverse=True)
