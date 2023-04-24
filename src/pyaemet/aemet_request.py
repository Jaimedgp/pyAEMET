""" AEMET API MODULE
-----------------

Python module to operate with AEMET OpenData API REST

:author Jaimedgp
"""

from datetime import date, datetime

import requests
import pandas as pd

from .types_classes.sites import SitesDataFrame

from .utilities.coordinates import transform_coordinates, get_site_address
from .utilities.dictionaries import SITES_TRANSLATION, OBSERVATIONS_TRANSLATION
from .utilities.curation import (
    update_fields,
    decimal_notation,
    convert_hours,
    remove_newline
    )



class _AemetApiRequest():
    """ Class to download data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        self.main_url = "https://opendata.aemet.es/opendata/api/"
        self._params = {"api_key": apikey}
        self._headers = {"cache-control": "no-cache",
                         "Accept": "application/json",
                         "Content-Type": "application/json",
                         }

    def _aemet_request(self, url):
        """
        """

        response = requests.request("GET",
                                    self.main_url+url,
                                    headers=self._headers,
                                    params=self._params
                                    )

        if response.ok:
            """
            Possible errores:
            -----------------

            429:
            404:
            401:
            """
            if response.text == "":
                return [{},
                        {"status":
                            "Nothing returned. Please check the API key"}
                       ]
            elif response.json()["estado"] == 200:
                data_url = response.json()["datos"]
                metadata_url = response.json()["metadatos"]

                return [requests.request("GET",
                                         data_url, headers=self._headers) \
                                .json(),
                        requests.request("GET",
                                         metadata_url,
                                         headers=self._headers) \
                                .json()
                        ]

        return [ {}, response.json() ]


class ClimaValues(_AemetApiRequest):
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        super().__init__(apikey)
        self.main_url += "valores/climatologicos/"

    def get_sites_info(self, old_dataframe: SitesDataFrame):
        """
        """

        data, metadata = self._aemet_request(url=("inventarioestaciones/" +
                                                  "todasestaciones/"))

        if not bool(data):
            return pd.DataFrame(columns=SITES_TRANSLATION.keys()), metadata

        data = pd.DataFrame(data) \
                 .rename(columns={v["id"]: k
                                  for k, v in SITES_TRANSLATION.items()}) \
                 .apply(transform_coordinates) \
                 .astype({k: v["dtype"]
                          for k, v in SITES_TRANSLATION.items()
                          if k in data})

        if (not all(data.columns.isin(old_dataframe.columns)) or
                (not data.equals(old_dataframe.loc[:, data.columns]))):

            data = data.merge(data.apply(get_site_address, axis=1,
                                         result_type="expand")
                                  .drop_duplicates(),
                              on=["latitude", "longitude"],
                              how='left'
                              ).drop_duplicates()

        else:
            old_dataframe.metadata.update({"access_date":
                                           datetime.now().isoformat()})
            return old_dataframe

        metadata = {k+"_aemet": v for k, v in metadata.items()}
        metadata["access_date"] = datetime.now().isoformat()
        metadata["fields"] = update_fields(data.columns,
                                           metadata.pop("campos_aemet"),
                                           SITES_TRANSLATION)

        return remove_newline(data), metadata

    def get_observations(
            self,
            fechaIniStr: date,
            fechaFinStr: date,
            idema: str
    ):
        """ Docstring """

        params = {"fechaIniStr": fechaIniStr.strftime("%Y-%m-%dT%H:%M:%SUTC"),
                  "fechaFinStr": fechaFinStr.strftime("%Y-%m-%dT%H:%M:%SUTC"),
                  "idema": idema
                  }

        data, metadata = self._aemet_request(url=("diarios/datos/fechaini/" +
                                                  "{fechaIniStr}/fechafin/" +
                                                  "{fechaFinStr}/estacion/" +
                                                  "{idema}"
                                                  ).format(**params))

        if not bool(data):
            return (pd.DataFrame(columns=OBSERVATIONS_TRANSLATION.keys()),
                    metadata)

        data = pd.DataFrame(data) \
                 .drop(["nombre", "provincia"], axis=1) \
                 .rename(columns={v["id"]: k
                                  for k, v in OBSERVATIONS_TRANSLATION.items()
                                  }) \
                 .replace({"Ip": "0,05", "Varias": "-1", "Acum": None}) \
                 .apply(decimal_notation, axis=1)

        data = data.astype({k: v["dtype"]
                            for k, v in OBSERVATIONS_TRANSLATION.items()
                            if k in data.columns}) \
                   .apply(convert_hours)

        metadata = {k+"_aemet": v for k, v in metadata.items()}
        metadata["access_date"] = datetime.now().isoformat()
        metadata["fields"] = update_fields(data,
                                           metadata.pop("campos_aemet"),
                                           OBSERVATIONS_TRANSLATION)

        return remove_newline(data), metadata
