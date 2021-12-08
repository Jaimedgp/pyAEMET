"""
Utilities
-----------

:author Jaimedgp
"""

from pandas import Series


def _coordinates(coordinate: str):
    """
    Convert AEMET_API longitude or latitude angles in degrees, minutes and
    seconds into float number in degrees

    E -> +       |    W -> -
    N -> +       |    S -> -

    :param coordinate: longitude or latitude angle
        e.g.: 425432N => +42º54'32"
    :returns: coordinate in float degrees. e.g.: 42.9089º
    """

    signo = {"E": 1, "W": -1, "N": 1, "S": -1}

    orientation = coordinate[-1]
    grados = float(coordinate[:2])
    minutes = float(coordinate[2:4]) / 60
    seconds = float(coordinate[4:6]) / 3600

    return signo[orientation]*(grados+minutes+seconds)


def transform_coordinates(
        sites: Series,
        columns: list = ["latitude", "longitude"]
):
    """
    """

    if sites.name in columns:
        sites = sites.apply(_coordinates)

    return sites
