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

        self.sites = self.get_sites()

    def _request_data(self, url):
        """ Docstring """

        # PONER AQUI EL TRATAMIENTO DEL ERROR AL REALIZAR DEMASIADAS CONSULTAS
        request = requests.request("GET",
                                   self.main_url +
                                   self.clima_url +
                                   url,
                                   headers=self.headers,
                                   params=self.api).json()

        if request['estado'] == 200:
            data = requests.request("GET",
                                    request['datos'],
                                    headers=self.headers,
                                    params=self.api).json()
            metadata = requests.request("GET",
                                        request['metadatos'],
                                        headers=self.headers,
                                        params=self.api).json()
        else:
            data, metadata = {}, {}

        return_values = pd.DataFrame.from_dict(data)
        return_values.attrs = {"estado": request['estado'],
                               "descripcion": request["descripcion"],
                               "metadatos": metadata}

        return return_values

    def get_sites(self):
        """ Obtain all AEMET sites information """

        self.sites = pd.read_pickle("~/Repositories/pyAEMET/doc/sites.pkl")

        new_sites = self._request_data("inventarioestaciones/todasestaciones/")

        if new_sites["indicativo"].isin(self.sites["indicativo"]).all():
            return self.sites

        print("Updating sites database...")

        included_st = self.sites[
                self.sites["indicativo"].isin(new_sites["indicativo"])
                ].copy()
        not_included_st = new_sites[
                ~new_sites["indicativo"].isin(self.sites["indicativo"])
                ].copy()

        not_included_st[["latitud",
                         "longitud"]
                        ] = not_included_st[["latitud",
                                             "longitud"]
                                            ].applymap(convert_coordinates)

        not_included_st = get_site_address(not_included_st.rename(
            columns={"latitud": "latitude",
                     "longitud": "longitude"}))

        self.sites = pd.concat([included_st,
                                not_included_st]
                               ).astype({'latitude': 'float64',
                                         'altitud': 'float64',
                                         'longitude': 'float64'
                                         })

        return self.sites

    def get_near_sites(self, lat, long, n_near=3):
        """ Obtain the n nearest AEMET sites to the location given by
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

        n_sites["dist"] = calc_dist_to([n_sites["latitude"].values,
                                        n_sites["longitude"].values],
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

    def get_data(self, sites, start, end=date.today()):
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

        if isinstance(sites, str):
            sites = [sites]
        elif isinstance(sites, list):
            pass
        elif isinstance(sites, pd.DataFrame):
            sites = list(sites["indicativo"].values)

        for st in sites:
            for i, (j, k) in enumerate(split_dt):

                to_obtain = self._request_data(
                    "diarios/datos/" +
                    "fechaini/" + str(j) +
                    "T00:00:00UTC/" +
                    "fechafin/" + str(k) +
                    "T23:59:59UTC/" +
                    "estacion/" + st + "/")

                if not isinstance(to_obtain, bool):
                    data += [to_obtain]
                else:
                    print(to_obtain)


        data_pd = pd.concat(data).replace({"Ip": "0,05", "Varias": "-2:00"})

        return decimal_notation(data_pd, notation=",").drop(["nombre",
                                                             "provincia",
                                                             "altitud"],
                                                            axis=1)
