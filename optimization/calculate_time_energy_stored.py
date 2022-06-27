import pandas as pd


def calculate_time_energy_stored(row, *, storage_technology, temporal_results):
    """
    Calculate how long the energy that is released in a particular row has been stored for
    """
    timestamp_current = row.name
    timestamp_previous = timestamp_current - pd.Timedelta(hours=1)

    # Return 0 if its the first timestamp
    if timestamp_previous not in temporal_results.index:
        return 0

    # Calculate the energy stored in the current and previous timestamp
    energy_stored_current = row[f"energy_stored_{storage_technology}_MWh"]
    energy_stored_previous = temporal_results[f"energy_stored_{storage_technology}_MWh"].loc[timestamp_previous]
    energy_delta = energy_stored_current - energy_stored_previous

    # Return 0 if the battery hasn't released energy
    if energy_delta >= 0:
        return 0

    # Set the weighted time and energy stored and loop over all timestamps that lie in the past
    weighted_time = 0
    energy_stored_min = energy_stored_previous
    reversed_history = temporal_results.loc[timestamp_previous::-1]
    for timestamp, energy_stored in reversed_history[f"energy_stored_{storage_technology}_MWh"].iteritems():
        # Continue if the energy stored is not less than the minimum stored energy already encountered
        if energy_stored >= energy_stored_min:
            continue

        # Add the weighted time difference to to the time and update the minimum energy stored variable
        hour_delta = (timestamp_current - timestamp).total_seconds() / 3600
        weighted_time += hour_delta * ((energy_stored_min - max(energy_stored, energy_stored_current)) / -energy_delta)
        energy_stored_min = energy_stored

        # Stop the for loop if all energy released has been accounted for
        if energy_stored <= energy_stored_current:
            break

    # Return the weighted average of time the energy was stored
    return weighted_time
