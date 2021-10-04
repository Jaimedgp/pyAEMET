"""
            AEMET API MODULE

    Python module to operate with AEMET OpenData API

    @author Jaimedgp
"""

from time import sleep
from datetime import date

import requests
import pandas as pd

from pyaemet.utilities import (split_date, decimal_notation, calc_dist_to,
                               convert_coordinates, get_site_address)


class AEMETAPI():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        self.main_url = "https://opendata.aemet.es/opendata/api"
        self.clima_url = "/valores/climatologicos/"
        # self.api = "?api_key=" + apikey
        self.api = {"api_key": apikey}
        self.headers = {'cache-control': "no-cache"}

        self.sites = None

    def get_sites(self):
        """ Obtain all AEMET sites information """

        self.sites = pd.read_csv("~/Repositories/pyAEMET/prueba.csv")

        request = requests.request("GET",
                                   self.main_url +
                                   self.clima_url +
                                   "inventarioestaciones/todasestaciones/",
                                   headers=self.headers,
                                   params=self.api).json()

        if request['estado'] == 200:
            data = requests.request("GET",
                                    request['datos'],
                                    headers=self.headers,
                                    params=self.api).json()

        new_sites = pd.DataFrame.from_dict(data)

        if (new_sites["indicativo"].isin(self.sites["indicativo"]).all()):
            return self.sites

        for col in ["latitud", "longitud"]:
            new_sites[col] = new_sites.apply(
                lambda df, col: convert_coordinates(df[col]), axis=1, col=col)

        self.sites = get_site_address(new_sites.rename(
                                      columns={"latitud": "latitude",
                                               "longitud": "longitude"}))

        return self.sites

    def get_data(self, site, start, end=date.today()):
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
                site: AEMET station identification named 'indicativo' in
                    AEMET sites dataset
                start:
                end: Default today date
            @return:
                pandas DataFrame with climate data between dates for station_id
                station.
        """

        split_dt = split_date(start, end)
        data = []

        if isinstance(site, str):
            site = [site]
        elif isinstance(site, list):
            pass
        elif isinstance(site, pd.DataFrame):
            site = list(site["indicativo"].values)

        for st in site:
            for i, (j, k) in enumerate(split_dt):
                downloaded = False

                while not downloaded:
                    to_obtain = requests.request(
                        "GET",
                        self.main_url +
                        self.clima_url +
                        "diarios/datos/" +
                        "fechaini/" + str(j) +
                        "T00:00:00UTC/" +
                        "fechafin/" + str(k) +
                        "T23:59:59UTC/" +
                        "estacion/" + st + "/",
                        headers=self.headers,
                        params=self.api).json()

                    if ("Espere al siguiente minuto" in
                            to_obtain['descripcion']):
                        print(to_obtain['estado'])
                        print("Number of requests exceed. Sleeping 1 minute")
                        sleep(35)
                    else:
                        break

                if to_obtain['estado'] == 200:
                    data_json = requests.request("GET",
                                                 to_obtain["datos"],
                                                 headers=self.headers,
                                                 params=self.api).json()
                    data += data_json
                elif to_obtain['estado'] == 404:
                    print("%s %i-%i: %s" % (st,
                                            j.year, k.year,
                                            to_obtain['descripcion']))
                else:
                    print(to_obtain['estado'])

        data_pd = pd.DataFrame.from_dict(data).replace({"Ip": "0,05",
                                                        "Varias": -2})

        return decimal_notation(data_pd, notation=",").drop(["nombre",
                                                             "provincia",
                                                             "altitud"],
                                                            axis=1)

    def get_near_sites(self, lat, long, n_near=3):
        """
            Obtain the n nearest AEMET sites to the location given by
            lattitude and longitude

            @params:
                lat: latitude of the location
                long: longitude of the location
                n: number of nearest sites to return
            @return:
                pandas DataFrame with information about the n nearest sites
                and their distance to the location
        """

        if self.sites is None:
            self.sites = self.get_sites()

        n_sites = self.sites.copy()

        n_sites["dist"] = calc_dist_to([n_sites["latitud"].values,
                                        n_sites["longitud"].values],
                                       [lat, long])

        return n_sites.sort_values(by=['dist'], ascending=True)[:n_near]

    def get_sites_by(self, city=None, province=None, ccaa=None):
        """ Get all the AEMET monitoring sites in a city, province or
            autonomous community (ccaa).

            @params:
                city: string with city name.
                    Default: None
                province: string with province (or subregion) name. If city
                    is provided, the province is ignore. Default: None
                ccaa: string with autonomus community (or region). If province
                    is provided, the ccaa is ignore. Default: None
            @return:
                pandas DataFrame with AEMET monitoring sites in the city,
                province or ccaa information
        """

        # CHECK THAT AT LEAST ONE PARAMETER IS NOT NONE

        if city is not None:
            filter_sites = self.sites[self.sites["City"] == city]
        elif province is not None:
            filter_sites = self.sites[self.sites["Subregion"] == province]
        elif ccaa is not None:
            filter_sites = self.sites[self.sites["Region"] == ccaa]
        else:
            print("At least one parameter must be pass." +
                  " city, province or ccaa")
            return False

        if filter_sites.empty:
            print("No hay estaciones que satisfagan los criterios")
            return False

        return filter_sites
