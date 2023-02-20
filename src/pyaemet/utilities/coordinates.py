"""
Utilities
-----------

:author Jaimedgp
"""

from pandas import Series, DataFrame, concat
from geocoder import arcgis


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


def get_address(lat, long):
    """
    Obtain the district, city, province and Autonomus community
    of a coordiante.

    :param lat: float of the latitude coordinate in degrees
    :param long: float of the longitude coordinate in degrees

    :return: pandas DataFrame with the latitude, longitude, district, city,
        province and autonomus community
    """

    address_data = arcgis([lat, long],
                          method='reverse').json["raw"]["address"]

    address_data.update({"latitude": lat,
                         "longitude": long})

    columns = ["District", "City",
               "Subregion", "Region",
               "latitude", "longitude"]

    return Series({k.lower(): v for k, v in address_data.items() if k in columns})


def get_site_address(row):
    """
    Obtain the district, city, province and Autonomus community of a
    coordiante.

    :params row: pandas Serie with latitude and longitude coordinates
        as columns.
    :return: pandas Serie with the latitude, longitude, district, city,
        province and autonomus community
    """

    return get_address(row["latitude"], row["longitude"])
