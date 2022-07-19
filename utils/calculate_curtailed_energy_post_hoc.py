import validate


def calculate_curtailed_energy_post_hoc(row, *, config):
    """
    Calculate the actual curtailed energy for a given timestamp
    """
    assert validate.is_series(row)
    assert validate.is_config(config)

    # Calculate the total energy losses
    total_losses = row.production_total_MW - row.demand_MW

    # Calculate the actual interconnection losses
    interconnection_losses = 0
    for interconnection_type in config["interconnections"]["efficiency"]:
        if f"net_export_{interconnection_type}_MW" in row:
            efficiency = config["interconnections"]["efficiency"][interconnection_type]
            net_export = row[f"net_export_{interconnection_type}_MW"]
            if net_export < 0:
                interconnection_losses += (1 / efficiency - 1) * abs(net_export)

    # Calculate the actual storage losses
    storage_losses = 0
    for storage_technology in config["technologies"]["storage"]:
        efficiency = config["technologies"]["storage"][storage_technology]["roundtrip_efficiency"] ** 0.5
        net_storage_flow = row[f"net_storage_flow_{storage_technology}_MW"]
        if net_storage_flow > 0:
            storage_losses += (1 - efficiency) * net_storage_flow
        else:
            storage_losses += (1 / efficiency - 1) * abs(net_storage_flow)

    # Calculate the curtailed energy
    return total_losses - interconnection_losses - storage_losses
