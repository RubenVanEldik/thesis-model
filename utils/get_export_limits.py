import utils
import validate


def get_export_limits(bidding_zone, *, config, type, index, direction="export"):
    """
    Find the relevant export limits for a bidding zone
    """
    assert validate.is_bidding_zone(bidding_zone)
    assert validate.is_config(config)
    assert validate.is_interconnection_type(type)
    assert validate.is_datetime_index(index)
    assert validate.is_interconnection_direction(direction)

    filepath = f"./input/interconnections/{config['model_year']}/{type}.csv"
    interconnections = utils.read_csv(filepath, parse_dates=True, index_col=0, header=[0, 1])

    # Remap the export limits from the model year to the selected years
    interconnections = index.to_series().apply(lambda timestamp: interconnections.loc[timestamp.replace(year=config["model_year"])])

    relevant_interconnections = []
    for country in config["countries"]:
        for zone in country["bidding_zones"]:
            interconnection = (bidding_zone, zone) if direction == "export" else (zone, bidding_zone)
            if interconnection in interconnections:
                relevant_interconnections.append(interconnection)
    return interconnections[relevant_interconnections]
