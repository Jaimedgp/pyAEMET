"""
AEMET API MODULE
-----------------

Python module to operate with AEMET OpenData API REST

:author Jaimedgp
"""

from datetime import datetime
import requests
import pandas as pd

from types_classes.sites import SitesDataFrame
from utilities.coordinates import transform_coordinates


sites_translation = \
{
    "latitude": {"id": "latitud",
                 "dtype": "float64"},
    "longitude": {"id": "longitud",
                  "dtype": "float64"},
    "altitude": {"id": "altitud",
                 "dtype": "float64"},
    "name": {"id": "nombre",
             "dtype": "string"},
    "site": {"id": "indicativo",
             "dtype": "string"},
    "provincia_aemet": {"id": "provincia",
                        "dtype": "string"},
    "synindic": {"id": "indsinop",
                 "dtype": "string"},
}


def _aemet_request(url: str, params: dict, headers: dict):
    """
    """

    if "api_key" not in params.keys():
        raise AttributeError("No 'api_key' found.")

    response = requests.request("GET",
                                url,
                                headers=headers,
                                params=params
                                )

    if response.ok:
        if response.json()["estado"] == 429:
            data, metadata = {}, response.json()
        if response.json()["estado"] == 200:
            data_url = response.json()["datos"]
            metadata_url = response.json()["metadatos"]

            data = requests.request("GET",
                                    data_url, headers=headers) \
                           .json()
            metadata = requests.request("GET",
                                        metadata_url, headers=headers) \
                               .json()

        if response.json()["estado"] == 404:
            data, metadata = {}, response.json()
        if response.json()["estado"] == 401:
            data, metadata = {}, response.json()

    else:
        data, metadata = {}, response.json()

    return data, metadata


class _AemetApiRequest():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        self.main_url = "https://opendata.aemet.es/opendata/api/"
        self._params = {"api_key": apikey}
        self._headers = {"cache-control": "no-cache",
                         "Accept": "application/json",
                         "Content-Type": "application/json",
                         }

    def get_sites_info(self):
        """
        """

        data, metadata = _aemet_request(url=(self.main_url +
                                             "valores/climatologicos/" +
                                             "inventarioestaciones/" +
                                             "todasestaciones/"),
                                        params=self._params,
                                        headers=self._headers)

        if not bool(data):
            raise TypeError("No sites found")

        data = pd.DataFrame(data) \
                 .rename(columns={v["id"]: k
                                  for k, v in sites_translation.items()}) \
                 .apply(transform_coordinates) \
                 .astype({k: v["dtype"]
                          for k, v in sites_translation.items()})

        metadata = {k+"_aemet": v for k, v in metadata.items()}
        metadata["access_date"] = datetime.now().isoformat()
        metadata["fields"] = {k: v for k, v in
                              [self.redo_fields(i)
                               for i in metadata.pop("campos_aemet")]}

        return SitesDataFrame(data=data, library="pyaemet", metadata=metadata)

    @staticmethod
    def redo_fields(field):
        """
        """

        key, = [k for k, v in sites_translation.items()
                if v["id"] == field["id"]]
        value = sites_translation[key]
        value["aemet"] = field

        return (key, value)
