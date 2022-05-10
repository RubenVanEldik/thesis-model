import validate


def write_text(filepath, text):
    """
    Store a string as .txt file
    """
    assert validate.is_filepath(filepath, suffix=".txt")
    assert validate.is_string(text, min_length=1)

    with open(filepath, "w") as f:
        f.write(text)
