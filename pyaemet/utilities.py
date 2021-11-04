"""
            AEMET API MODULE

    Python module to operate with AEMET OpenData API

    @author Jaimedgp
"""

import pandas as pd
import numpy as np
import geocoder as gc


def calc_dist_to(coor1, coor2, radius=6371):
    """
    Calculate distance between locations given in latitudes and
    longitudes coordinates. The distance is calculated using the
    following equation:

        dist = radius *
            arcocos{cos(lat1 - lat2) -
                    cos(lat1)*cos(lat2)*[1 cos(long1 - long2)]}

    :param coor1: list of coordinates of first location
        e.g.: [latitude,longitude]
    :param corr2: list of coordinates of second location
        e.g.: [latitude,longitude]
    :param radius: earth radius

    :returns: distance between the two locations in kilometers
        (Due to radius is given in km)
    """

    coor1 = np.deg2rad(coor1)
    coor2 = np.deg2rad(coor2)

    dist = radius * np.arccos(np.cos(coor1[0] - coor2[0]) -
                              np.cos(coor1[0]) *
                              np.cos(coor2[0]) *
                              (1 - np.cos(coor1[1] - coor2[1])))

    return dist


def update_sites(old_dataframe, new_dataframe):
    """ Docstring """

    not_included = new_dataframe[~new_dataframe.isin(old_dataframe)].dropna()

    return pd.concat([old_dataframe, get_site_address(not_included)])


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

    addresses = pd.concat(rows_sites)

    return dataframe.merge(addresses,
                           on=["latitude", "longitude"],
                           how='left'
                           ).drop_duplicates()
