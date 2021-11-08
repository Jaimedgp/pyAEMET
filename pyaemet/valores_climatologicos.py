"""
            AEMET API MODULE

    Python module to operate with AEMET OpenData API

    @author Jaimedgp
"""

from datetime import date
import tempfile as tmpfl
from dateutil.relativedelta import relativedelta
import pandas as pd
import requests

from pyaemet.aemet_api_request import _AemetApiUse
from pyaemet import __dataset_doi__
from pyaemet.utilities import calc_dist_to, update_sites


class AemetClima():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        self._aemet_api = _AemetApiUse(apikey)
        self._old_dataset = self._read_sites_database()

    def _get_clima(self, params):
        """ Docstring """

        url = ("/api/valores/climatologicos/diarios/" +
               "datos/fechaini/{fechaIniStr}/" +
               "fechafin/{fechaFinStr}/estacion/{idema}").format(**params)

        aemet_data, aemet_metadata = self._aemet_api.request_info(url=url)
        aemet_data = pd.DataFrame.from_dict(aemet_data)

        if aemet_data.empty:
            return aemet_data

        aemet_data = aemet_data.replace({"Ip": "0,05",
                                         "Varias": "-1"
                                         })
        aemet_data = self._decimal_notation(aemet_data)
        aemet_data = self._columns_dtypes(aemet_data)

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
                                               self._coordinates)
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
            estacion = ",".join(estacion.indicativo
                                        .drop_duplicates()
                                        .to_list())

        parameters = self._split_date(fecha_ini, fecha_fin)

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

        if any(type(x) != list for x in kwargs.values()):
            print("Los valores de filtrados deben ser listas")
            return None
        if any(x not in aemet_sites.columns for x in kwargs.keys()):
            print("Alguno de los criterios de filtrado seleccionados no " +
                  "corresponde a la \ninformacion de las estaciones.\n" +
                  "Revisa que los criterios correspondan a las columnas del" +
                  "pd.DataFrame devuelto \npor la función " +
                  "AemetClima.sites_info()")
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

    def estaciones_curacion(self, fecha_ini, fecha_fin=date.today(),
            umbral=0.75, variables='all', save_folder=None, **kwargs):
        """ Docstring """

        if "estacion" in kwargs.keys():
            if isinstance(kwargs["estacion"], pd.DataFrame):
                estaciones = kwargs["estacion"].copy()
                id_estaciones = kwargs["estacion"].indicativo
            else:
                if (isinstance(kwargs["estacion"], list) or
                    isinstance(kwargs["estacion"], str)):
                    estaciones = pd.DataFrame(
                        columns={"indicativo": kwargs["estacion"]})
                else:
                    print("El argumento estacion no es valido, por favor pase " +
                        "el indicativo de la estacion\n en forma de 'string' " +
                        "o lista de 'string' o pase un dataframe con la " +
                        "informacion\n de la estacion")
                    return False

            estaciones["suficientesDatos"] = False
            for indicativo in estaciones.indicativo:
                data = self.clima_diaria(indicativo, fecha_ini, fecha_fin)
                if data.empty:
                    continue

                is_enough = self._have_enough(data,
                                              fecha_ini, fecha_fin,
                                              umbral, variables)

                estaciones.loc[estaciones["indicativo"] == indicativo,
                               "suficientesDatos"] = is_enough

                if is_enough and save_folder is not None:
                    data.to_csv(save_folder+indicativo+".csv")
            else:
                return estaciones

        elif any(x in kwargs.keys() for x in ("latitud",
                                              "longitud",
                                              "n_cercanas")):
            estaciones = self.estaciones_cerca(latitud=kwargs["latitud"],
                                               longitud=kwargs["longitud"],
                                               n_cercanas=kwargs["n_cercanas"])

            for indicativo in estaciones.indicativo:
                data = self.clima_diaria(indicativo, fecha_ini, fecha_fin)
                if data.empty:
                    continue

                is_enough = self._have_enough(data_frame=data,
                                              start_date=fecha_ini,
                                              end_date=fecha_fin,
                                              threshold=umbral,
                                              columns=variables)

                if is_enough:
                    if save_folder is not None:
                        data.to_csv(save_folder+indicativo+".csv")
                    return estaciones[estaciones.indicativo == indicativo]
            else:
                return False

    @staticmethod
    def _have_enough(data_frame, start_date, end_date,
                     threshold=0.75, columns='all'):
        """ Docstring """

        if any(col not in data_frame.columns for col in columns):
            return False
        if columns == 'all':
            columns = data_frame.columns

        duration = (end_date - start_date).days + 1  # (a, b] => [a, b]
        amount_data = data_frame[columns].notna().sum() / duration

        return (amount_data >= threshold).all()

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def _columns_dtypes(aemet_dataframe):
        """ Docstring """

        for col in aemet_dataframe.columns:
            if "hora" in col and aemet_dataframe.dtypes[col] == 'object':
                aemet_dataframe[col] = pd.to_numeric(
                    aemet_dataframe[col].str.split(":").str[0])

        return aemet_dataframe.astype({'fecha': 'datetime64',
                                    'indicativo': 'str'})

    @staticmethod
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
