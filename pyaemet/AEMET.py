"""
            AEMET API MODULE

    Python module to operate with AEMET OpenData API

    @author Jaimedgp
"""


import numpy as np
import pandas as pd
import tempfile as tmpfl

import requests

from dateutil.relativedelta import relativedelta


class AEMET_API():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API"""

        self.main_url = "https://opendata.aemet.es/opendata/api"
        self.clima_url = "/valores/climatologicos/"
        self.api = "?api_key=" + apikey

        self.stations = None

    def get_stations(self):
        """ Obtain all AEMET stations information """

        to_obtain = requests.get((self.main_url +
                                  self.clima_url +
                                  "inventarioestaciones/todasestaciones/" +
                                  self.api
                                  ), {'accept': 'application/json'}).json()

        data = requests.get(to_obtain["datos"],
                            {'accept': 'application/json'}).json()

        self.stations = pd.DataFrame.from_dict(data)

        for col in ["latitud", "longitud"]:
            self.stations[col] = self.stations.apply(
                lambda df, col:
                AEMET_API.convert_coordiantes(df[col]),
                axis=1, col=col
                )

        return self.stations

    def get_nearest_stations(self, lat, long, n=3):
        """
            Obtain the n nearest AEMET stations to the location given by
            lattitude and longitude

            @params:
                lat: latitude of the location
                long: longitude of the location
                n: number of nearest stations to return
            @return:
                pandas DataFrame with information about the n nearest stations
                and their distance to the location
        """

        if self.stations is None:
            self.stations = self.get_stations()

        n_stations = self.stations.copy()

        n_stations["dist"] = AEMET_API.calc_dist(
            [n_stations["latitud"].values,
             n_stations["longitud"].values],
            [lat, long])

        return n_stations.sort_values(by=['dist'], ascending=True)[:n]

    def get_data(self, dates, station_id):
        """
            Download climate data from AEMET station. Aemet include same
            values that have to be replace to make the dataset readable
            for everyone.

            - Replace coma '0,0' decimals to dot '0.0'
            - Replace strings in numerical columns by a numeric key

            |  Code  |            Meaning           |  New Value   |
            |:------:|:----------------------------:|:------------:|
            |   Ip   | prec < 0.1mm (Inappreciable) |     0.05     |
            | Varios |         Various hours        |     -2       |

            @params:
                dates: list of dates -> [start_dt, end_dt]
                station_id: AEMET station identification named 'indicativo' in
                AEMET stations dataset
            @return:
                pandas DataFrame with climate data between dates for station_id
                station.
        """

        split_dt = AEMET_API.split_date(dates[0], dates[1])
        data = []

        for i, (j, k) in enumerate(split_dt):
            to_obtain = requests.get((self.main_url +
                                      self.clima_url +
                                      "diarios/datos/" +
                                      "fechaini/" + str(j) + "T00:00:00UTC/" +
                                      "fechafin/" + str(k) + "T23:59:59UTC/" +
                                      "estacion/" + station_id + "/" +
                                      self.api
                                      ), {'accept': 'application/json'}
                                     ).json()

            print("%s/%s: %s" % (i+1, len(split_dt), to_obtain['descripcion']))

            if to_obtain['descripcion'] == "exito":
                data_json = requests.get(to_obtain["datos"],
                                         {'accept': 'application/json'}).json()
                data += data_json
            else:
                return None

        data_pd = pd.DataFrame.from_dict(data) .replace({"Ip": "0,05",
                                                         "Varias": -2})

        return AEMET_API.dot_decimals(data_pd)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def convert_coordiantes(coordinate):
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
