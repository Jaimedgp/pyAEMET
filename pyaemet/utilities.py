import tempfile as tmpfl

import numpy as np
import pandas as pd
import geocoder as gc

from dateutil.relativedelta import relativedelta
from datetime import datetime


def split_date(start, end):
    """
        Check if interval between start_dt and end_dt is bigger than 5
        years, and if so, divide it in interval of less than 5 years.

        @params:
            start: beginning date of interval
            end: ending date of interval
        @return:
            list of tuplas with inteval of less than 5 years between
            start date and end date
    """

    n_intervals = relativedelta(end, start).years // 4

    return ([(start.replace(year=start.year + (i-1)*4),
              start.replace(year=start.year + (i)*4))
             for i in range(1, n_intervals+1)]
            + [(start.replace(year=start.year + n_intervals*4), end)])


def decimal_notation(dataframe, notation=","):
    """
        Replace coma '0,0' decimals to dot '0.0'

        @params:
            dataframe: pandas DataFrame with decimals in original notation
            notation: original notation. Default: ','
        @return:
            pandas DataFrame with float decimal with dot notation
    """

    tmp_fl = tmpfl.NamedTemporaryFile().name

    dataframe.to_csv(tmp_fl, sep=";", index=False)

    return pd.read_csv(tmp_fl, sep=";", decimal=notation)


def calc_dist_to(coor1, coor2, radius=6371):
    """
        Calculate distance between locations given in latitudes and
        longitudes coordinates. The distance is calculated using the
        following equation:

            dist = radius *
                arcocos{cos(lat1 - lat2) -
                        cos(lat1)*cos(lat2)*[1 cos(long1 - long2)]}

        @params:
            coor1: list of coordinates of first location
                    e.g.: [latitude,longitude]
            corr2: list of coordinates of second location
                    e.g.: [latitude,longitude]
            radius: earth radius
        @return:
            distance between the two locations in kilometers (Due to radius
            is given in km)
    """

    coor1 = np.deg2rad(coor1)
    coor2 = np.deg2rad(coor2)

    dist = radius * np.arccos(np.cos(coor1[0] - coor2[0]) -
                              np.cos(coor1[0]) *
                              np.cos(coor2[0]) *
                              (1 - np.cos(coor1[1] - coor2[1])))

    return dist


def convert_coordinates(coordinate):
    """ Convert AEMET_API longitude or latitude angles in degrees, minutes and
        seconds into float number in degrees

        E -> +       |    W -> -
        N -> +       |    S -> -

        @params:
            coordinate: longitude or latitude angle
                e.g.: 425432N => +42º54'32"
        @return:
            coordinate in float degrees. e.g.: 42.9089º
    """

    signo = {"E": 1, "W": -1, "N": 1, "S": -1}

    orientation = coordinate[-1]
    grados = float(coordinate[:2])
    minutes = float(coordinate[2:4]) / 60
    seconds = float(coordinate[4:6]) / 3600

    return signo[orientation]*(grados+minutes+seconds)


def get_address(lat, long):
    """ Obtain the district, city, province and Autonomus community
        of a coordiante.

        @params:
            lat: float of the latitude coordinate in degrees
            long: float of the longitude coordinate in degrees
        @return:
            pandas DataFrame with the latitude, longitude, district, city,
            province and autonomus community
    """

    address_data = gc.arcgis([lat, long],
                             method='reverse').json["raw"]["address"]

    address_data.update({"latitude": lat,
                         "longitude": long})

    return pd.DataFrame(pd.Series(address_data)).T[["District",
                                                    "City",
                                                    "Subregion",
                                                    "Region",
                                                    "CountryCode",
                                                    "latitude",
                                                    "longitude"]]


def get_site_address(dataframe):
    """ Obtain the district, city, province and Autonomus community
        of a coordiante.

        @params:
            dataframe: pandas DataFrame with latitude and longitude coordinates
            as columns.
        @return:
            pandas DataFrame with the latitude, longitude, district, city,
            province and autonomus community
    """

    rows_sites = [get_address(x["latitude"],
                              x["longitude"]
                              ) for i, x in dataframe.iterrows()]

    addresses = pd.concat(rows_sites).rename(columns={"Latitude": "latitude",
                                                      "Longitude": "longitude"}
                                             )

    return dataframe.merge(addresses, on=["latitude", "longitude"])


def horavariable_type(row):
    """ AEMET horavariable dtype """

    if row['horatmin'] == "-2:00":
        return datetime(1, 1, 1, 0, 0)
    if row['horatmin'] == "00:00":
        return datetime(row['fecha'].year,
                        row['fecha'].month,
                        row['fecha'].day,
                        0, 0)
    hora = pd.to_datetime(row['horatmin'], format="%H:%M",)

    return datetime(row['fecha'].year,
                    row['fecha'].month,
                    row['fecha'].day,
                    hora.hour, hora.minute)
