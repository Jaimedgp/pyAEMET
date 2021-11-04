"""
            AEMET API MODULE

    Python module to operate with AEMET OpenData API

    @author Jaimedgp
"""

from datetime import date
import tempfile as tmpfl
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import geocoder as gc
import requests

from pyaemet.aemet_api_request import _AemetApiUse
from pyaemet import __dataset_doi__


class AemetClima():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        self._aemet_api = _AemetApiUse(apikey)
        self._old_dataset = _read_sites_database()

    def _get_clima(self, params):
        """ Docstring """

        url = ("/api/valores/climatologicos/diarios/" +
               "datos/fechaini/{fechaIniStr}/" +
               "fechafin/{fechaFinStr}/estacion/{idema}").format(**params)

        aemet_data, aemet_metadata = self._aemet_api.request_info(url=url)

        aemet_data = pd.DataFrame.from_dict(aemet_data) \
                                 .replace({"Ip": "0,05",
                                           "Varias": "-1"
                                           })
        aemet_data = _decimal_notation(aemet_data)
        aemet_data = _columns_dtypes(aemet_data)

        aemet_data.attrs = aemet_metadata

        return aemet_data

    def _get_sites(self):
        """ Docstring """

        url = ("/api/valores/climatologicos/" +
               "inventarioestaciones/todasestaciones/")

        aemet_st, aemet_metadata = self._aemet_api.request_info(url=url)

        aemet_st = pd.DataFrame.from_dict(aemet_st) \
                               .astype({"altitud": "float64"}) \
                               .rename(columns={"provincia": "provinciaAemet"})

        aemet_st[["latitud",
                  "longitud"]] = aemet_st[["latitud",
                                           "longitud"]].applymap(
                                               _coordinates)
        aemet_st.attrs = aemet_metadata

        return aemet_st

    def estaciones_info(self):
        """ Docstring """

        aemet_st = self._get_sites() \
                       .sort_values('indicativo') \
                       .reset_index(drop=True)

        database_metadata = {"Distrito": "Distrito. No siempre disponible",
                             "ciudad": "Ciudad o Municipio",
                             "provincia": "Provincia",
                             "CA": "Comunidad Autonoma",
                             "pais": "Codigo del pais"
                             }

        if not aemet_st.equals(self._old_dataset[aemet_st.columns]):
            print("Actualizando...")
            estaciones = update_sites(self._old_dataset, aemet_st) \
                .rename(columns={"District": "distrito",
                                 "City": "ciudad",
                                 "Subregion": "provincia",
                                 "Region": "CA",
                                 "CountryCode": "pais"
                                 })
        else:
            estaciones = self._old_dataset

        estaciones.attrs = {**aemet_st.attrs, **database_metadata}

        return estaciones

    def clima_diaria(self, estacion, fecha_ini, fecha_fin=date.today()):
        """ Docstring """

        if isinstance(estacion, list):
            estacion = ",".join(estacion)
        if isinstance(estacion, pd.DataFrame):
            estacion = ",".join(estacion.indicativo.drop_duplicates(
                ).to_list())

        parameters = _split_date(fecha_ini, fecha_fin)

        aemet_data = pd.DataFrame()

        for param in parameters:
            param["idema"] = estacion

            download = self._get_clima(param)

            aemet_data = pd.concat([aemet_data, download])
            aemet_data.attrs.update(download.attrs)

        return aemet_data

    def estaciones_loc(self, **kwargs):
        """
        Get all the AEMET monitoring sites in a city, province or
        autonomous community (ccaa).

        :param city: string with city name.
            Default: None
        :param province: string with province (or subregion) name. If city
            is provided, the province is ignore. Default: None
        :param ccaa: string with autonomus community (or region). If province
            is provided, the ccaa is ignore. Default: None

        :returns: pandas DataFrame with AEMET monitoring sites in the city,
            province or ccaa information
        """

        aemet_sites = self.estaciones_info()

        if aemet_sites.columns.isin(kwargs.keys()).sum() != len(kwargs):
            print("""
Alguno de los criterios de filtrado seleccionados no corresponde a informacion
de las estaciones.
Revisa que los criterios correspondan a las columnas del pd.DataFrame devuelto
por la función AemetClima.sites_info()
""")

            return None

        for ky, vl in kwargs.items():
            aemet_sites = aemet_sites[aemet_sites[ky].isin(vl)].dropna()

        return aemet_sites

    def estaciones_cerca(self, latitud, longitud, n_cercanas=3):
        """
        Obtain the n nearest AEMET sites to the location given by
        lattitude and longitude

        :param lat: latitude of the location
        :param long: longitude of the location
        :param n_cercanas: number of nearest sites to return

        :returns: pandas DataFrame with information about the n nearest sites
            and their distance to the location
        """

        aemet_st = self.estaciones_info()

        aemet_st["distancia"] = calc_dist_to([aemet_st["latitud"].values,
                                              aemet_st["longitud"].values],
                                             [latitud, longitud])

        return aemet_st.sort_values(by=['distancia'],
                                    ascending=True)[:n_cercanas]


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


def _read_sites_database():
    """ Docstring """

    zenodo_url = ("https://zenodo.org/api/records/" +
                  __dataset_doi__.split(".")[-1])
    req = requests.get(zenodo_url,
                       {'accept': 'application/json'})

    if not req.ok:
        return False

    for file in req.json()["files"]:
        if file["type"] == "pkl":
            myfile = requests.get(file["links"]["self"])
            break

    with tmpfl.NamedTemporaryFile() as tmp_fl:
        tmp_fl.write(myfile.content)
        return pd.read_pickle(tmp_fl.name)


def _split_date(start, end, min_years=4):
    """
    Check if interval between start_dt and end_dt is bigger than 5
    years, and if so, divide it in interval of less than 5 years.

    :param start: beginning date of interval
    :param end: ending date of interval

    :returns: list of tuplas with inteval of less than 5 years between
        start date and end date
    """

    date_format = "%Y-%m-%dT%H:%M:%SUTC"
    min_years_delta = relativedelta(years=min_years)

    n_delta = relativedelta(end, start).years // min_years + 1

    interval_dates = [start+(i*min_years_delta) for i in range(0, n_delta)]
    interval_dates += [end]

    params = [{"fechaIniStr": interval_dates[j].strftime(date_format),
               "fechaFinStr": interval_dates[j+1].strftime(date_format)
               } for j in range(0, n_delta)]

    return params


def _coordinates(coordinate):
    """
    Convert AEMET_API longitude or latitude angles in degrees, minutes and
    seconds into float number in degrees

    E -> +       |    W -> -
    N -> +       |    S -> -

    :param coordinate: longitude or latitude angle
        e.g.: 425432N => +42º54'32"
    :returns: coordinate in float degrees. e.g.: 42.9089º
    """

    signo = {"E": 1, "W": -1, "N": 1, "S": -1}

    orientation = coordinate[-1]
    grados = float(coordinate[:2])
    minutes = float(coordinate[2:4]) / 60
    seconds = float(coordinate[4:6]) / 3600

    return signo[orientation]*(grados+minutes+seconds)


def _columns_dtypes(aemet_dataframe):
    """ Docstring """

    for col in aemet_dataframe.columns:
        if "hora" in col and aemet_dataframe.dtypes[col] == 'object':
            aemet_dataframe[col] = pd.to_numeric(
                aemet_dataframe[col].str.split(":").str[0])

    return aemet_dataframe.astype({'fecha': 'datetime64',
                                   'indicativo': 'str'})


def _decimal_notation(dataframe, notation=","):
    """
    Replace coma '0,0' decimals to dot '0.0'

    :param dataframe: pandas DataFrame with decimals in original notation
    :param notation: original notation. Default: ','

    :returns: pandas DataFrame with float decimal with dot notation
    """

    tmp_fl = tmpfl.NamedTemporaryFile().name

    dataframe.to_csv(tmp_fl, sep=";", index=False)

    return pd.read_csv(tmp_fl, sep=";", decimal=notation)
