def create_datetime_index(index, year):
    """
    Change a multiIndex (01.01, 23) into an ISO datetime string
    """
    new_index = []
    for [date, hour] in index:
        day, month, *rest = date.split(".")
        hour = str(hour - 1).rjust(2, "0")
        new_index.append(f"{year}-{month}-{day}T{hour}:00:00Z")
    return new_index
