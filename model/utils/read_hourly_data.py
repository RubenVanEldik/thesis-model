import utils
import validate


def read_hourly_data(filepath, *, start=None, end=None):
    """
    Returns the hourly data, if specified only for a specific date range
    """
    assert validate.is_filepath(filepath, suffix=".csv")
    assert validate.is_date(start, required=False)
    assert validate.is_date(end, required=False)

    hourly_data = utils.read_csv(filepath, parse_dates=True, index_col=0)

    # Set the time to the beginning and end of the start and end date respectively
    start = start.strftime("%Y-%m-%d 00:00:00") if start else None
    end = end.strftime("%Y-%m-%d 23:59:59") if end else None

    # Return the hourly data
    return hourly_data[start:end]
