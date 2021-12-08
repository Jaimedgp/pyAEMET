"""
AEMET API MODULE
-----------------

Python module to operate with AEMET OpenData API REST

:author Jaimedgp
"""

# from copy import copy
from pkg_resources import resource_stream

from types_classes.sites import SitesDataFrame
from aemet_request import _AemetApiRequest
# from pyaemet.types_classes.observations import ObservationsDataFrame


class AemetClima():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        self._aemet_request = _AemetApiRequest(apikey=apikey)
        self.aemet_sites = self._saved_sites_info()

    @staticmethod
    def _saved_sites_info():
        """
        """

        folder = "data/sites/"

        data_fl = resource_stream(__name__, folder+'data.csv')
        metadata_fl = resource_stream(__name__, folder+'metadata.json')

        return SitesDataFrame.open_from(data_fl=data_fl,
                                        metadata_fl=metadata_fl)

    def sites_info(self, update=True):
        """
        Update Sites information from AEMET
        """

        if not update:
            return self.aemet_sites.copy()

        return self._aemet_request.get_sites_info()

    def sites_in(
            self,
            update_first: bool = False,
            **kwargs,
    ):

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
    ):

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
