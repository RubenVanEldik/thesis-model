import dropbox

import utils
import validate

# Initialize the Dropbox client
dropbox_access_token = utils.getenv("DROPBOX_ACCESS_TOKEN")
client = dropbox.Dropbox(dropbox_access_token)


def upload_to_dropbox(path, dropbox_path):
    """
    Upload a file or directory (recursively) to Dropbox
    """
    assert validate.is_directory_path(path) or validate.is_filepath(path)
    assert validate.is_directory_path(dropbox_path)

    # Add the file/directory name to the Dropbox path
    dropbox_path /= path.name

    # If the path is a file, upload it
    if path.is_file() and path.suffix in [".csv", ".yaml", ".png"]:
        client.files_upload(open(path, "rb").read(), "/" + str(dropbox_path), mute=True)

    # If the path is a directory, call this function for each of its items
    elif path.is_dir():
        for path in path.iterdir():
            upload_to_dropbox(path, dropbox_path)
