"""
AEMET API MODULE
-----------------

Python module to operate with AEMET OpenData API REST

:author Jaimedgp
"""

import json
import pandas as pd
# from copy import copy

from pyaemet.types_classes.sites import SitesDataFrame
# from pyaemet.types_classes.observations import ObservationsDataFrame

from pkg_resources import resource_stream


class AemetClima():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        self._aemet_api = {"apikey": apikey}
        self.aemet_sites = self._saved_sites_info()

    @staticmethod
    def open_sites(
            data_fl: str = None,
            metadata_fl: str = None,
            folder_name: str = None
    ):
        """
        """

        if data_fl is None:
            if folder_name is None:
                raise(KeyError("Not correct file path"))
            else:
                data_fl = folder_name + "data.pkl"
        if metadata_fl is None:
            if folder_name is None:
                raise(KeyError("Not correct file path"))
            else:
                metadata_fl = folder_name + "metadata.json"

        return SitesDataFrame(
            data=pd.read_pickle(data_fl),
            library="pyaemet",
            metadata=json.load(metadata_fl)
            )

    @staticmethod
    def _saved_sites_info():
        """
        """

        folder = "data/sites/"

        data_fl = resource_stream(__name__, folder+'data.pkl')
        metadata_fl = resource_stream(__name__, folder+'metadata.json')

        return AemetClima.open_sites(data_fl=data_fl, metadata_fl=metadata_fl)

    def sites_info(self, update=True):
        """
        Update Sites information from AEMET
        """

        if not update:
            return self.aemet_sites.copy()

        return None

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
