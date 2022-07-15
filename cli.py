import optimization
import utils
import validate


def _ask_for_file(directory):
    """
    Ask the user which file in a specific directory should be returned
    """
    assert validate.is_directory_path(directory)

    # Get the directory
    assert directory.is_dir(), f"No directory called '{directory.name}' could be found"

    # Get all files in the directory
    file_names = [filepath for filepath in directory.iterdir() if filepath.suffix == ".yaml"]
    assert len(file_names), f"No files were found in the {directory} directory"

    print(f"Files in {directory}:")
    for index, file_name in enumerate(file_names):
        print(f"   {index + 1}. {file_name.stem}{file_name.suffix}")

    # Ask for a specific file
    file_number = input(f"\nSelect a file: ")
    assert file_number.isnumeric(), f"'{file_number}' is not a number"
    assert 0 < int(file_number) <= len(file_names), f"'{file_number}' is not between 1 and {len(file_names)}"

    return utils.read_yaml(file_names[int(file_number) - 1])


if __name__ == "__main__":
    print(f"\n\n{'-' * 40}\n\n")

    # Ask and get the configuration file
    config = _ask_for_file(utils.path("cli", "configs"))

    # Ask for the name of the run
    default_run_name = utils.get_next_run_name()
    config["name"] = default_run_name + input(f"\n\nName of the run: {default_run_name}")

    # Run the optimization
    optimization.run(config, output_folder=utils.path("output", config["name"]))
