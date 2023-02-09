"""
AEMET API MODULE
-----------------

Python module to operate with AEMET OpenData API REST

:author Jaimedgp
"""

import os
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from pkg_resources import resource_stream

from tqdm import tqdm
import numpy as np
from pandas import Series, DataFrame, concat

from .types_classes.sites import SitesDataFrame, NearSitesDataFrame
from .types_classes.observations import ObservationsDataFrame
from .aemet_request import ClimaValues
from .utilities.dictionaries import V1_TRANSLATION


logger = logging.getLogger()


class AemetClima():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey: str):
        """ Get the needed API key"""

        self._aemet_request = ClimaValues(apikey=apikey)
        self._aemet_sites = self._saved_sites_info()

    @property
    def aemet_sites(self):
        return self._aemet_sites

    @aemet_sites.setter
    def aemet_sites(self, value):
        if isinstance(value, SitesDataFrame):
            return value
        raise TypeError("AemetClima.aemet_sites must be a "
                        + "SitesDataFrame object")

    @staticmethod
    def _saved_sites_info() -> SitesDataFrame:
        """
        """

        folder = "static/sites/"

        data_fl = resource_stream(__name__, folder+'data.csv')
        metadata_fl = resource_stream(__name__, folder+'metadata.json')

        return SitesDataFrame.open_from(data_fl=data_fl,
                                        metadata_fl=metadata_fl)

    def sites_info(self, update: bool = True) -> SitesDataFrame:
        """
        Update Sites information from AEMET
        """

        if self.aemet_sites.empty or update:
            new_sites, new_metadata = self._aemet_request \
                                          .get_sites_info(
                                              old_dataframe=self.aemet_sites)
            self.aemet_sites = SitesDataFrame(data=new_sites,
                                              library="pyaemet",
                                              metadata=new_metadata)

        return self.aemet_sites.copy()

    def estaciones_info(self, actualizar: bool = True):
        """ Obtener informacion de las estaciones meteorologicas de la AEMET
            Deprecado en la version 2.0.0

        """

        logger.warning("<AemetClima>.estaciones_info() is deprecated since "
                       + "version 2.0.0. Please use <AemetClima>.sites_info() "
                       + "instead and take advantage of <SitesDataFrame> "
                       + "new options.")

        return self.sites_info(update=actualizar) \
                   .as_dataframe() \
                   .rename(columns=V1_TRANSLATION)

    def sites_in(
        self,
        update_first: bool = False,
        **kwargs,
        ) -> SitesDataFrame:
        """
        Get all the AEMET monitoring sites in a city, province (subregion) or
        autonomous community (region).

        Parameters
        ----------
            city: string with city name. Default: None
            province: string with province (or subregion) name. If city
                is provided, the province is ignore. Default: None
            ccaa: string with autonomus community (or region). If province
                is provided, the ccaa is ignore. Default: None

        Returns
        -------
            pandas DataFrame with AEMET monitoring sites in the city,
            province or ccaa information
        """

        # Check if an update is needed first
        if self.aemet_sites.empty or update_first:
            self.sites_info()

        return self.aemet_sites.filter_in(**kwargs,)

    def estaciones_loc(
        self,
        actualizar: bool = False,
        **kwargs,
        ) -> DataFrame:
        """
        Parameters
        ----------

        Returns
        -------
        """

        logger.warning("<AemetClima>.estaciones_loc() is deprecated since "
                       + "version 2.0.0. Please use <AemetClima>.sites_in() "
                       + "instead and take advantage of <SitesDataFrame> "
                       + "new options.")

        translation = {vl: ky for ky, vl in V1_TRANSLATION.items()}
        new_kwargs = {}
        for ky, vl in kwargs.items():
            new_kwargs[translation[ky]] = vl

        return self.sites_in(**new_kwargs, update_first=actualizar) \
                   .as_dataframe() \
                   .rename(columns=V1_TRANSLATION)

    def near_sites(
        self,
        latitude: float | int,
        longitude: float | int,
        n_near: int | None = 100,
        max_distance: float | int = 6237.0,
        update_first: bool = False,
        ) -> NearSitesDataFrame:
        """
        Get all the AEMET monitoring sites in

        Parameters
        ----------

        Returns
        -------
            pandas DataFrame with AEMET monitoring sites in
        """

        # Check if an update is needed first
        if self.aemet_sites.empty or update_first:
            sites = self.sites_info()
        else:
            sites = self.aemet_sites

        return sites.filter_at(
            latitude,
            longitude,
            n_near,
            max_distance)

    def estaciones_cerca(
        self,
        latitud: int | float,
        longitud: int | float,
        n_cercanas: int | None = 100,
        max_distancia: int | float = 6237.0,
        actualizar: bool = False,
        ) -> DataFrame | None:
        """
        Parameters
        ----------
        Return sites in
        """

        logger.warning("<AemetClima>.estaciones_cerca() is deprecated since "
                       + "version 2.0.0. Please use <AemetClima>.near_sites() "
                       + "instead and take advantage of <SitesDataFrame> "
                       + "new options.")

        # Check if an update is needed first
        if self.aemet_sites.empty or actualizar:
            sites = self.sites_info()
        else:
            sites = self.aemet_sites

        return sites.filter_at(latitude=latitud,
                               longitude=longitud,
                               n_near=n_cercanas,
                               max_distance=max_distancia) \
                    .as_dataframe() \
                    .rename(columns=V1_TRANSLATION)


    def daily_clima(
        self,
        site,
        start_dt: date | datetime,
        end_dt: date | datetime = date.today()
        ) -> ObservationsDataFrame:
        """
        Parameters
        ----------
        """

        if isinstance(site, str):
            pass
        elif isinstance(site, list):
            site = ",".join(site)
        elif isinstance(site, DataFrame):
            site = ",".join(site.site.drop_duplicates().to_list())

        data_list = []
        metadata = {}

        # Split dates in intervals where: end_dt - start_dt < 5 years
        splited_dates = self._split_date(start_dt, end_dt)

        for start, end in splited_dates:
            data, meta = self._aemet_request \
                             .get_observations(fechaIniStr=start,
                                               fechaFinStr=end,
                                               idema=site)
            data_list.append(data)
            metadata.update(meta)

        return ObservationsDataFrame(data=concat(data_list),
                                     library="pyaemet",
                                     metadata=metadata)

    def clima_diaria(
        self,
        estacion,
        fecha_ini: date | datetime,
        fecha_fin: date | datetime = date.today()
        ) -> ObservationsDataFrame:
        """
        Parameters
        ----------
        estacion,
        fecha_ini
        fecha_fin
        """

        logger.warning("<AemetClima>.clima_diaria() is deprecated since "
                       + "version 2.0.0. Please use <AemetClima>.daily_clima() "
                       + "instead and take advantage of <SitesDataFrame> "
                       + "new options.")

        return self.daily_clima(site=estacion,
                                start_dt=fecha_ini,
                                end_dt=fecha_fin)

    def sites_curation(
        self,
        start_dt: date | datetime,
        sites: ( str | list
               | Series | DataFrame
               | SitesDataFrame | NearSitesDataFrame),
        end_dt: date | datetime = date.today(),
        threshold: float = 0.75,
        variables: str | list = 'all',
        save_folder: str | os.PathLike | None = ...,
        ) -> SitesDataFrame | NearSitesDataFrame | DataFrame:
        """

        Parameters
        ----------
        sites : str,
        start_dt : date
            Start date to define curation period in which the porcentage of
            abailable data is going to be defined and determinied if the
            aemet's site is enough

        ent_dt : date, default `date.today()`
            End date to define curation period in which the porcentage of
            abailable data is going to be defined and determinied if the
            aemet's site is enough. By default current date is taken

        sites : str, list, Series, DataFrame, SitesDataFrame,
            NearSitesDataFrame, default None
            Aemete's sites selection for data curation. This information should
            be obtained previously by <AemetClima.near_sites>,
            <AemetClima.sites_in>, <AemetClima.estaciones_loc> or
            <AemetClima.estaciones_cerca>.

        threshold : float, default 0.75 (75%)
            Minimum porpotion of data able a site must has to be consider

        variables :  str, list, default 'all'
            Columns' names in which the `_have_enough` function is going to be
            parse. The default value 'all' is set to parse the function to the
            full abailable dataframe.

        save_folder : str. default None
            Path to the folder in which the data downloaded during the process
            is going to be saved. If `save_folder` is not set to a False value,
            all data will be saved, independent of the amount of data abailable
            in `variables`

        Return
        ----------
        SitesDataFrame
            If 'distance' column is pass, the nearest site with enough data is
            returned,
        """

        # To know if the curantion must end when a
        # nearest site with enough data is found
        for_nearest = False

        # Convert sites parameter to SitesDataFrame
        if isinstance(sites, (str, list)):
            _sites = self.sites_in(site=sites)
        elif isinstance(sites, NearSitesDataFrame):
            _sites = sites.sort_values(by='distance', ascending=False)
            for_nearest = True
        elif isinstance(sites, (Series, DataFrame, SitesDataFrame)):
            try:
                _sites = self.sites_in(site=sites["site"])
            except KeyError:
                _sites = self.sites_in(site=sites["indicativo"])
        else:
            _sites = sites

        if not _sites or _sites.empty:
            raise KeyError("No sites' information passed")

        _sites["has_enough"] = False
        _sites["amount"] = np.nan

        for st in tqdm(_sites.site):
            data = self.daily_clima(site=st, start_dt=start_dt, end_dt=end_dt)
            if data.empty:
                continue

            is_enough = self._have_enough(data,
                                          start_date=start_dt,
                                          end_date=end_dt,
                                          threshold=threshold,
                                          columns=variables)

            if for_nearest:
                return _sites.loc[_sites["site"] == st]

            _sites.loc[_sites["site"] == st, "suficientesDatos"] = is_enough

            if is_enough and save_folder is not None:
                data.to_csv(save_folder+st+".csv")

        return _sites

    @staticmethod
    def _have_enough(data_frame, start_date, end_date,
                     threshold=0.75, columns: str | list = 'all'):
        """ Docstring """

        if any(col not in data_frame.columns for col in columns):
            return False
        if columns == 'all':
            columns = data_frame.columns

        duration = (end_date - start_date).days + 1  # (a, b] => [a, b]
        amount_data = data_frame[columns].notna().sum() / duration

        return (amount_data >= threshold).all()

    @staticmethod
    def _split_date(start_dt: date, end_dt: date, min_years: int = 4) -> list:
        """
        Check if interval between start_dt and end_dt is bigger than 5
        years, and if so, divide it in interval of less than 5 years.

        :param start: beginning date of interval
        :param end: ending date of interval

        :returns: list of tuplas with inteval of less than 5 years between
            start date and end date
        """

        min_years_delta = relativedelta(years=min_years)
        n_delta = relativedelta(end_dt, start_dt).years // min_years + 1

        interval_dates = [start_dt+(i*min_years_delta)
                          for i in range(0, n_delta)]
        interval_dates += [end_dt]

        return [(interval_dates[j], interval_dates[j+1])
                for j in range(0, n_delta)]
