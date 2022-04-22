"""
AEMET API MODULE
-----------------

Python module to operate with AEMET OpenData API REST

:author Jaimedgp
"""

# from copy import copy
from datetime import date
from dateutil.relativedelta import relativedelta
from pandas import DataFrame, concat
from pkg_resources import resource_stream

from pyaemet.types_classes.sites import SitesDataFrame, NearSitesDataFrame
from pyaemet.types_classes.observations import ObservationsDataFrame

from pyaemet.aemet_request import ClimaValues


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

        folder = "data/sites/"

        data_fl = resource_stream(__name__, folder+'data.csv')
        metadata_fl = resource_stream(__name__, folder+'metadata.json')

        return SitesDataFrame.open_from(data_fl=data_fl,
                                        metadata_fl=metadata_fl)

    def sites_info(self, update=True) -> SitesDataFrame:
        """
        Update Sites information from AEMET
        """

        if update:
            new_sites, new_metadata = self._aemet_request \
                                          .get_sites_info(
                                                old_dataframe=self.aemet_sites)
            self.aemet_sites = SitesDataFrame(data=new_sites,
                                              library="pyaemet",
                                              metadata=new_metadata)
        else:
            self.aemet_sites = self._saved_sites_info()

        return self.aemet_sites.copy()

    def sites_in(
            self,
            update_first: bool = False,
            **kwargs,
    ) -> SitesDataFrame:
        """
        Return sites in
        """

        # Check if an update is needed first
        if update_first:
            sites = self.sites_info()
        else:
            sites = self.aemet_sites.copy()

        return sites.filter_in(**kwargs,)

    def near_sites(
            self,
            latitude: float,
            longitude: float,
            n_near: int = 100,
            max_distance: float = 6237.0,
            update_first: bool = False,
    ) -> NearSitesDataFrame:
        """
        Return sites in
        """

        # Check if an update is needed first
        if update_first:
            sites = self.sites_info()
        else:
            sites = self.aemet_sites.copy()

        return sites.filter_at(
            latitude,
            longitude,
            n_near,
            max_distance)

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
