import dropbox
import shutil

import utils
import validate

# Initialize the Dropbox client
dropbox_access_token = utils.getenv("DROPBOX_ACCESS_TOKEN")
if dropbox_access_token:
    client = dropbox.Dropbox(dropbox_access_token)


def upload_to_dropbox(path, dropbox_path):
    """
    Upload a file or directory to Dropbox
    """
    assert validate.is_directory_path(path) or validate.is_filepath(path)
    assert validate.is_directory_path(dropbox_path)

    if "client" not in globals():
        print("Could not upload to Dropbox because DROPBOX_ACCESS_TOKEN was not set")
        return

    # If the path is a directory upload the files as a ZIP file
    if path.is_dir():
        shutil.make_archive(str(path), "zip", str(path))
        client.files_upload(open(f"{path}.zip", "rb").read(), f"/{dropbox_path / path.name}.zip", mute=True)
    else:
        client.files_upload(open(path, "rb").read(), f"/{dropbox_path / path.name}", mute=True)
