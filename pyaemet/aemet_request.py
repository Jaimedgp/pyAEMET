""" AEMET API MODULE
-----------------

Python module to operate with AEMET OpenData API REST

:author Jaimedgp
"""

from datetime import date, datetime

import requests
import pandas as pd

from utilities.coordinates import transform_coordinates, get_site_address
from utilities.curation import update_fields, decimal_notation, convert_hours

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

observations_translation = \
{
    "date": {"id": "fecha",
             "dtype": "datetime64"},
    "site": {"id": "indicativo",
             "dtype": "string"},
    "altitude": {"id": "altitud",
                 "dtype": "float64"},
    "temp_avg": {"id": "tmed",
                 "dtype": "float64"},
    "precipitation": {"id": "prec",
                      "dtype": "float64"},
    "temp_min": {"id": "tmin",
                 "dtype": "float64"},
    "temp_max": {"id": "tmax",
                 "dtype": "float64"},
    "hr_temp_min": {"id": "horatmin",
                    "dtype": "object"},
    "hr_temp_max": {"id": "horatmax",
                    "dtype": "object"},
    "wnd_dir": {"id": "dir",
                "dtype": "float64"},
    "wnd_spd": {"id": "velmedia",
                "dtype": "float64"},
    "wnd_gst": {"id": "racha",
                "dtype": "float64"},
    "hr_wnd_gst": {"id": "horaracha",
                   "dtype": "object"},
    "press_max": {"id": "presMax",
                  "dtype": "float64"},
    "hr_press_max": {"id": "horaPresMax",
                     "dtype": "object"},
    "press_min": {"id": "presMin",
                  "dtype": "float64"},
    "hr_press_min": {"id": "horaPresMin",
                     "dtype": "object"},
    "hr_sun": {"id": "sol",
               "dtype": "float64"},
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
            return pd.DataFrame(columns=sites_translation.keys()), metadata

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
        metadata["fields"] = update_fields(data,
                                           metadata.pop("campos_aemet"),
                                           sites_translation)

        return data, metadata

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

        data, metadata = _aemet_request(url=(self.main_url +
                                             "valores/climatologicos/" +
                                             "diarios/datos/fechaini/" +
                                             "{fechaIniStr}/fechafin/" +
                                             "{fechaFinStr}/estacion/" +
                                             "{idema}"
                                             ).format(**params),
                                        params=self._params,
                                        headers=self._headers)

        if not bool(data):
            return (pd.DataFrame(columns=observations_translation.keys()),
                    metadata)

        data = pd.DataFrame(data) \
                 .drop(["nombre", "provincia"], axis=1) \
                 .rename(columns={v["id"]: k
                                  for k, v in observations_translation.items()
                                  }) \
                 .replace({"Ip": "0,05", "Varias": "-1"}) \
                 .apply(decimal_notation, axis=1)
        data = data.astype({k: v["dtype"]
                            for k, v in observations_translation.items()
                            if k in data.columns}) \
                   .apply(convert_hours)

        metadata = {k+"_aemet": v for k, v in metadata.items()}
        metadata["access_date"] = datetime.now().isoformat()
        metadata["fields"] = update_fields(data,
                                           metadata.pop("campos_aemet"),
                                           observations_translation)

        return data, metadata
