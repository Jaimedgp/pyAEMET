import tempfile as tmpfl

import numpy as np
import pandas as pd
import geocoder as gc

from dateutil.relativedelta import relativedelta


def split_date(start_dt, end_dt):
    """
        Check if interval between start_dt and end_dt is bigger than 5
        years, and if so, divide it in interval of less than 5 years.

        @params:
            start_dt: beginning date of interval
            end_dt: ending date of interval
        @return:
            list of tuplas with inteval of less than 5 years between
            start_dt and end_dt
    """

    if relativedelta(end_dt, start_dt).years < 5:
        dates = [(start_dt, end_dt)]
    else:
        new_dt = end_dt.replace(year=end_dt.year - 4)
        new_end = end_dt
        dates = [(new_dt, new_end)]

        while relativedelta(new_dt, start_dt).years > 5:
            dates.append((new_dt, new_end))

            new_end = new_dt
            new_dt = new_dt.replace(year=end_dt.year - 4)

        dates.append((start_dt, new_dt))

    return dates


def dot_decimals(data_coma):
    """
        Replace coma '0,0' decimals to dot '0.0'

        @params:
            data_coma: pandas DataFrame with decimals in coma notation
        @return:
            pandas DataFrame with float decimal with dot notation
    """

    tmp_fl = tmpfl.NamedTemporaryFile().name

    data_coma.to_csv(tmp_fl, sep=";", index=False)
    data_dots = pd.read_csv(tmp_fl, sep=";", decimal=",")

    return data_dots


def calc_dist(pos1, pos2, radius=6371):
    """
        Calculate distance between locations given in latitudes and
        longitudes coordinates. The distance is calculated using the
        following equation:

            dist = radius *
                arcocos{cos(lat1 - lat2) -
                        cos(lat1)*cos(lat2)*[1 cos(long1 - long2)]}

        @params:
            pos1: list of coordinates of first location
                    e.g.: [latitude,longitude]
            pos1: list of coordinates of second location
                    e.g.: [latitude,longitude]
            radius: earth radius
        @return:
            distance between the two locations in kilometers (Due to radius
            is given in km)
    """

    pos1 = np.deg2rad(pos1)
    pos2 = np.deg2rad(pos2)

    dist = radius * np.arccos(np.cos(pos1[0] - pos2[0]) -
                              np.cos(pos1[0]) *
                              np.cos(pos2[0]) *
                              (1 - np.cos(pos1[1] - pos2[1])))

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
    """ obtain the city, province and Autonomus community of a coordiante """

    address_data = gc.arcgis([lat, long],
                             method='reverse').json["raw"]["address"]

    address_data.update({"Latitude": lat,
                         "Longitude": long})

    return pd.DataFrame(pd.Series(address_data)).T[["District",
                                                    "City",
                                                    "Subregion",
                                                    "Region",
                                                    "CountryCode",
                                                    "Latitude",
                                                    "Longitude"]]


def for_dataframe(a):

    return a.merge(pd.concat([get_address(x["Latitude"],
                                          x["Longitude"]
                                          ) for i, x in a.iterrows()
                              ]),
                   on=["Latitude", "Longitude"])
