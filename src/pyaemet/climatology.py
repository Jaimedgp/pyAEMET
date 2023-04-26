"""
This is the AemetClima class that interfaces with AEMET's Climatic Station
Web Service API. It has several functions to request information about
climatic stations and to download meteorological observations data.
"""

import os
import logging
from datetime import date, datetime
from typing import Optional, Union
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
    """
    The `AemetClima` class is used to interface with AEMET's Climatic
    Station Web Service API. It makes available a number of functions
    for requesting information about the climatic stations, and for
    downloading meteorological observations data.
    """

    def __init__(self, apikey):
        """
        Initialize the `AemetClima` class with a valid API Key.

        Parameters
        ----------
        apikey : str
            The API Key obtained from AEMET's web services.
        """

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
        Load the saved information about the AEMET climatic stations
        from a `SitesDataFrame`.

        Returns
        -------
        SitesDataFrame
            The dataframe containing the information of the AEMET
            climatic stations.
        """

        folder = "static/sites/"

        data_fl = resource_stream(__name__, folder+'data.csv')
        metadata_fl = resource_stream(__name__, folder+'metadata.json')

        return SitesDataFrame.open_from(data_fl=data_fl,
                                        metadata_fl=metadata_fl)

    def sites_info(self, update: bool = True) -> SitesDataFrame:
        """
        Get the information about the AEMET climatic stations.

        Parameters
        ----------
        update : bool, optional
            If `True`, the information about the AEMET climatic stations
            is updated from the AEMET Web Services.

        Returns
        -------
        SitesDataFrame
            The dataframe containing the information of the AEMET
            climatic stations.
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
        """
        Get the information about the AEMET climatic stations.

        .. deprecated:: 1.1.0
            Please use `sites_info()` instead and take advantage
            of `SitesDataFrame` new options.

        Parameters
        ----------
        actualizar : bool, optional
            If `True`, the information about the AEMET climatic stationsis updated from the AEMET Web Services.

        Returns
        -------
        pandas.DataFrame
            The dataframe containing the information of the AEMET
            climatic stations. The columns are named using the Spanish
            translation of their names.
        """

        logger.warning("<AemetClima>.estaciones_info() is deprecated since "
                       + "version 1.1.0. Please use <AemetClima>.sites_info() "
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
        Get information about climatic stations within a specified
        region or with specific characteristics.

        Parameters
        ----------
        update_first : bool, optional
            If True, the information about the climatic stations will be
            updated from the AEMET Web Services before filtering. The
            updated information will be saved to the `aemet_sites`
            attribute of the class instance.
        kwargs : dict
            Keyword arguments to be passed to the `filter_in` method of
            the `SitesDataFrame` class.

        Returns
        -------
        SitesDataFrame
            The filtered dataframe containing the information of the
            climatic stations.
        """

        # Check if an update is needed first
        if self.aemet_sites.empty or update_first:
            self.sites_info()

        # Filter the information of the climatic stations
        return self.aemet_sites.filter_in(**kwargs,)

    def estaciones_loc(
        self,
        actualizar: bool = False,
        **kwargs,
    ) -> Optional[DataFrame]:
        """
        Get location data for stations available in Aemet.

        .. deprecated:: 1.1.0
            Please use `sites_in()` instead and take advantage
            of `SitesDataFrame` new options.

        Parameters
        ----------
        actualizar : bool, optional
            Whether to update the data stored in memory. By default, False.
        **kwargs :
            Additional parameters to use in the search.

        Returns
        -------
        pd.DataFrame
            DataFrame with location information for stations.
        """

        logger.warning("<AemetClima>.estaciones_loc() is deprecated since "
                       + "version 1.1.0. Please use <AemetClima>.sites_in() "
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
        latitude: Union[float, int],
        longitude: Union[float, int],
        n_near: Optional[int] = 100,
        max_distance: Union[float, int] = 6237,
        update_first: bool = False,
    ) -> NearSitesDataFrame:
        """
        Retrieve information about climatic stations near a set of coordinates.

        Parameters
        ----------
        latitude : float, int
            Latitude of the location to search the nearest climatic stations.
        longitude : float, int
            Longitude of the location to search the nearest climatic stations.
        n_near : int, optional
            Number of nearest climatic stations to return, by default 100.
        max_distance : float, int, optional
            Maximum distance, in meters, to return the nearest climatic
            stations, by default 6237.0.
        update_first : bool, optional
            Flag to indicate if it is necessary to update the climatic
            stations information before filtering them, by default False.

        Returns
        -------
        NearSitesDataFrame
            DataFrame with the information of the nearest climatic stations.
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
        latitud: Union[int, float],
        longitud: Union[int, float],
        n_cercanas: Optional[int] = 100,
        max_distancia: Union[int, float] = 6237,
        actualizar: bool = False,
        ) -> Union[DataFrame]:
        """
        Retrieve information about climatic stations near a set of coordinates.

        .. deprecated:: 1.1.0
            Please use `near_sites()` instead and take advantage
            of `NearSitesDataFrame` new options.

        Parameters
        ----------
        latitud: int, float
            Latitude of the point
        longitud: int, float
            Longitude of the point
        n_cercanas: int, optional
            Number of closest stations to return. Default is 100
        max_distancia: int, float, optional
            Maximum distance in km to consider a station as 'nearby'
        actualizar: bool, optional
            Update the internal list of climatic stations. Default is False

        Returns:
        -------
        pandas.DataFrame
            DataFrame with the information of the closest climatic stations
        """

        logger.warning("<AemetClima>.estaciones_cerca() is deprecated since "
                       + "version 1.1.0. Please use <AemetClima>.near_sites() "
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

    def sites_curation(
        self,
        start_dt: Union[date, datetime],
        sites: Union[
            str, list, Series, DataFrame , SitesDataFrame, NearSitesDataFrame
        ],
        end_dt: Union[date, datetime] = date.today(),
        threshold: float = 0.75,
        variables: Union[str, list] = 'all',
        save_folder: Optional[Union[str, os.PathLike]] = ...,
        verbosity: bool = True,
        ) -> Union[SitesDataFrame, NearSitesDataFrame, DataFrame]:
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

        # To know if the curantion must end when a nearest site with
        # enough data is found
        for_nearest = False

        # Convert sites parameter to SitesDataFrame
        if isinstance(sites, (str, list)):
            _sites = self.sites_in(site=sites)
        elif isinstance(sites, NearSitesDataFrame):
            _sites = sites.sort_values(by='distance', ascending=False)
            for_nearest = True
        elif isinstance(sites, (Series, DataFrame, SitesDataFrame)):
            try:
                _sites = self.sites_in(site=list(sites["site"]))
            except KeyError:
                _sites = self.sites_in(site=list(sites["indicativo"]))
        else:
            _sites = sites

        if not isinstance(_sites, DataFrame) or _sites.empty:
            raise KeyError("No sites' information passed")

        _sites["has_enough"] = False
        _sites["amount"] = np.nan

        if verbosity:
            iteration = tqdm(_sites.site)
        else:
            iteration = _sites.site

        for st in iteration:
            data = self.daily_clima(site=st,
                                    start_dt=start_dt,
                                    end_dt=end_dt,
                                    verbosity=False)
            if data.empty:
                continue

            is_enough, amount = self._have_enough(data,
                                                  start_date=start_dt,
                                                  end_date=end_dt,
                                                  threshold=threshold,
                                                  columns=variables)

            _sites.loc[_sites["site"] == st, "has_enough"] = is_enough
            _sites.loc[_sites["site"] == st, "amount"] = amount

            if for_nearest:
                return _sites.loc[_sites["site"] == st]

            if is_enough and save_folder is not None:
                data.to_csv(save_folder+st+".csv")

        return _sites

    def estaciones_curacion(
        self,
        fecha_ini: Union[date, datetime],
        fecha_fin: Union[date, datetime] = date.today(),
        umbral: float = 0.75,
        variables: Union[str, list] = 'all',
        save_folder: Optional[str] = None,
        actualizar: bool = False,
        **kwargs
        ) -> Optional[DataFrame]:
        """ Docstring """

        logger.warning("<AemetClima>.estaciones_curacion() is deprecated "
                       + "since version 1.1.0. Please use "
                       + "<AemetClima>.sites_curation() instead and take "
                       + "advantage of <SitesDataFrame> and "
                       + "<NearSitesDataFrame> new options.")

        # Check if an update is needed first
        if self.aemet_sites.empty or actualizar:
            sites = self.sites_info()
        else:
            sites = self.aemet_sites

        return sites.sites_curation(start_dt=fecha_ini,
                                    end_dt=fecha_fin,
                                    threshold=umbral,
                                    variables=variables,
                                    save_folder=save_folder,
                                    ) \
                    .as_dataframe() \
                    .rename(columns=V1_TRANSLATION)

    def daily_clima(
        self,
        site,
        start_dt: Union[date, datetime],
        end_dt: Union[date, datetime] = date.today(),
        verbosity: bool = True
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

        if verbosity:
            splited_dates = tqdm(splited_dates)

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
        fecha_ini: Union[date, datetime],
        fecha_fin: Union[date, datetime] = date.today()
        ) -> ObservationsDataFrame:
        """
        """

        logger.warning("<AemetClima>.clima_diaria() is deprecated since "
                       + "version 1.1.0. Please use <AemetClima>.daily_clima() "
                       + "instead and take advantage of <SitesDataFrame> "
                       + "new options.")

        return self.daily_clima(site=estacion,
                                start_dt=fecha_ini,
                                end_dt=fecha_fin)

    @staticmethod
    def _have_enough(data_frame, start_date, end_date,
                     threshold=0.75, columns: Union[str, list] = 'all'):
        """ Docstring """

        if isinstance(columns, str):
            columns = [columns]

        if any(col not in data_frame.columns for col in columns):
            return False, 0.0
        if columns == 'all':
            columns = data_frame.columns

        duration = (end_date - start_date).days + 1  # (a, b] => [a, b]
        amount_data = data_frame[columns].notna().sum() / duration

        return [(amount_data >= threshold).all(), amount_data.mean()]

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
