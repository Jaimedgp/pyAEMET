"""
AEMET API MODULE
-----------------

Python module to operate with AEMET OpenData API REST

:author Jaimedgp
"""

import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from pkg_resources import resource_stream

from pandas import DataFrame, concat

from .types_classes.sites import SitesDataFrame, NearSitesDataFrame
from .types_classes.observations import ObservationsDataFrame
from .aemet_request import ClimaValues
from .utilities.dictionaries import V1_TRANSLATION


logger = logging.getLogger()


class AemetClima():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        self._aemet_request = ClimaValues(apikey=apikey)
        self.aemet_sites = self._saved_sites_info()

    @staticmethod
    def _saved_sites_info() -> SitesDataFrame:
        """
        """

        folder = "static/sites/"

        data_fl = resource_stream(__name__, folder+'data.csv')
        metadata_fl = resource_stream(__name__, folder+'metadata.json')

        return SitesDataFrame.open_from(data_fl=data_fl,
                                        metadata_fl=metadata_fl)

    def sites_info(self, update=True) -> SitesDataFrame:
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

    def estaciones_info(self, actualizar=True):
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
        :param city: string with city name.
            Default: None
        :param province: string with province (or subregion) name. If city
            is provided, the province is ignore. Default: None
        :param ccaa: string with autonomus community (or region). If province
            is provided, the ccaa is ignore. Default: None
        :returns: pandas DataFrame with AEMET monitoring sites in the city,
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
            latitude: float,
            longitude: float,
            n_near: int = 100,
            max_distance: float = 6237.0,
            update_first: bool = False,
    ) -> NearSitesDataFrame:
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
            latitud: float,
            longitud: float,
            n_cercanas=100,
            max_distancia: float = 6237.0,
            actualizar: bool = False,
    ) -> DataFrame:
        """
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
            start_dt: date,
            end_dt: date = date.today()
    ) -> ObservationsDataFrame:
        """
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
        fecha_ini: date,
        fecha_fin: date = date.today()
    ) -> ObservationsDataFrame:

        logger.warning("<AemetClima>.clima_diaria() is deprecated since "
                       + "version 2.0.0. Please use <AemetClima>.daily_clima() "
                       + "instead and take advantage of <SitesDataFrame> "
                       + "new options.")

        return self.daily_clima(site=estacion,
                                start_dt=fecha_ini,
                                end_dt=fecha_fin)

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
