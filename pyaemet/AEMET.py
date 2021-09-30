"""
            AEMET API MODULE

    Python module to operate with AEMET OpenData API

    @author Jaimedgp
"""

import pandas as pd

import requests

from time import sleep
from utilities import split_date, dot_decimals, calc_dist, convert_coordinates


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
                lambda df, col: convert_coordiantes(df[col]), axis=1, col=col)

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

        n_stations["dist"] = calc_dist([n_stations["latitud"].values,
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

        split_dt = split_date(dates[0], dates[1])
        data = []

        for i, (j, k) in enumerate(split_dt):
            downloaded = False

            while not downloaded:
                to_obtain = requests.get((self.main_url +
                                          self.clima_url +
                                          "diarios/datos/" +
                                          "fechaini/" + str(j) +
                                          "T00:00:00UTC/" +
                                          "fechafin/" + str(k) + "T23:59:59UTC/" +
                                          "estacion/" + station_id + "/" +
                                          self.api
                                          ), {'accept': 'application/json'}
                                         ).json()

                if "Espere al siguiente minuto" in to_obtain['descripcion']:
                    print("Number of requests exceed. Sleeping 1 minute")
                    sleep(35)
                else:
                    break

            if to_obtain['descripcion'] == "exito":
                data_json = requests.get(to_obtain["datos"],
                                         {'accept': 'application/json'}).json()
                data += data_json
            else:
                return None

        data_pd = pd.DataFrame.from_dict(data).replace({"Ip": "0,05",
                                                        "Varias": -2})

        return dot_decimals(data_pd)

    def get_data_
