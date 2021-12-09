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
from utilities.coordinates import transform_coordinates, get_site_address


sites_translation = \
{
    "site": {"id": "indicativo",
             "dtype": "string"},
    "name": {"id": "nombre",
             "dtype": "string"},
    "synindic": {"id": "indsinop",
                 "dtype": "string"},
    "latitude": {"id": "latitud",
                 "dtype": "float64"},
    "longitude": {"id": "longitud",
                  "dtype": "float64"},
    "altitude": {"id": "altitud",
                 "dtype": "float64"},
    "District": {"id": "distrito",
                 "dtype": "string"},
    "City": {"id": "ciudad",
             "dtype": "string"},
    "Subregion": {"id": "provincia",
                  "dtype": "string"},
    "Region": {"id": "Comunidad Autonoma",
               "dtype": "string"},
    "subregion_aemet": {"id": "provincia",
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

    def get_sites_info(self, old_dataframe: pd.DataFrame):
        """
        """

        data, metadata = _aemet_request(url=(self.main_url +
                                             "valores/climatologicos/" +
                                             "inventarioestaciones/" +
                                             "todasestaciones/"),
                                        params=self._params,
                                        headers=self._headers)

        if not bool(data):
            return SitesDataFrame(columns=sites_translation.keys(),
                                  library="pyaemet", metadata=metadata)

        data = pd.DataFrame(data) \
                 .rename(columns={v["id"]: k
                                  for k, v in sites_translation.items()}) \
                 .apply(transform_coordinates) \
                 .astype({k: v["dtype"]
                          for k, v in sites_translation.items()
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
            data = old_dataframe

        metadata = {k+"_aemet": v for k, v in metadata.items()}
        metadata["access_date"] = datetime.now().isoformat()
        metadata["fields"] = self.update_fields(data,
                                                metadata.pop("campos_aemet"))

        return SitesDataFrame(data=data, library="pyaemet", metadata=metadata)

    @staticmethod
    def update_fields(data, metadata):
        """
        """

        new_metadata = sites_translation.copy()

        for k, v in new_metadata.items():
            if k in data.columns:
                for i in metadata:
                    if i["id"] == v["id"]:
                        v["aemet"] = {k: v for k, v in i.items() if k != "id"}
                        break

        return new_metadata
