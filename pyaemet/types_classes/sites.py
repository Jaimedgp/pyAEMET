"""
SitesDataFrame
-----------------

"""

from pandas import DataFrame

import folium
import numpy as np


class SitesDataFrame(DataFrame):
    """

    """

    def __init__(
            self,
            data=None,
            index=None,
            columns=None,
            dtype=None,
            copy=None,
            metadata: dict = None,
    ):

        super().__init__(
            data=data,
            index=index,
            columns=columns,
            dtype=dtype,
            copy=copy
        )

        if metadata is None:
            metadata = {}
        object.__setattr__(self, "metadata", metadata)

    def plot_map(self):
        """
        plot map with the sites location
        """

        index_lat, = np.where(self.columns == "latitude")[0]
        index_lon, = np.where(self.columns == "longitude")[0]

        latitudes = self._get_column_array(index_lat)
        longitudes = self._get_column_array(index_lon)

        center = [np.mean([np.min(latitudes), np.max(latitudes)]),
                  np.mean([np.min(longitudes), np.max(longitudes)])]

        mapa = folium.Map(location=center, zoom_start=3)
        folium.LayerControl().add_to(mapa)

        for i in self.index:
            popup = "<strong>Name:</strong> %s" % (self._get_value(i, "name"))
            folium.Marker([self._get_value(i, "latitude"),
                           self._get_value(i, "longitude")],
                          popup=folium.Popup(popup, max_width=480),
                          tooltip="Click me!").add_to(mapa)

        object.__setattr__(self, "map", mapa)
        return mapa

    def filter_in(self, **kwargs):
        """
        """

        if any(type(x) != list for x in kwargs.values()):
            raise(TypeError("only list-like objects are allowed to be passed" +
                            " to filter_in(), you passed a [str]"))
        if any(x not in self.columns for x in kwargs.keys()):
            raise(KeyError("The keys passed to filter_in() does not match " +
                           "with SitesDataFrame columns"))

        sites = self.copy()
        for ky, vl in kwargs.items():
            sites = sites.__getitem__(sites.__getitem__(ky).isin(vl)).dropna()

        return SitesDataFrame(data=sites, metadata=self.metadata)

    def filter_at(
            self,
            latitude: float,
            longitude: float,
            n_near: int = 10,
            max_distance: float = 6237.0,
    ):
        """
        """

        sites_distance = self.calc_distance(latitude, longitude)

        sites_distance = sites_distance.__getitem__(
            sites_distance.__getitem__("distance") <=
            max_distance).sort_values(by=['distance'],
                                      ascending=True)[:(n_near+1)]

        return NearSitesDataFrame(ref_point=[latitude, longitude],
                                  data=sites_distance, metadata=self.metadata)

    def calc_distance(
            self,
            latitude: float,
            longitude: float,
            radius: float = 6371.0,
    ):

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

        coor1 = DataFrame(np.deg2rad(self.__getitem__(["latitude",
                                                       "longitude"])))
        latitude, longitude = np.deg2rad(latitude), np.deg2rad(longitude)

        new_data = self.copy()

        new_data.__setitem__(key="distance", value=coor1.apply(
                lambda row: radius *
                np.arccos(np.cos(row["latitude"] - latitude) -
                          np.cos(row["latitude"]) * np.cos(latitude) *
                          (1 - np.cos(row["longitude"] - longitude))
                          ), axis=1))

        return new_data


class NearSitesDataFrame(SitesDataFrame):
    """
    """

    def __init__(
            self,
            ref_point: [float, float],
            data=None,
            index=None,
            columns=None,
            dtype=None,
            copy=None,
            metadata=None,
    ):
        """
        """

        super().__init__(
            data=data,
            index=index,
            columns=columns,
            dtype=dtype,
            copy=copy,
            metadata=metadata,
        )

        self.metadata.update({"Reference Point": {"latitude": ref_point[0],
                                                  "longitude": ref_point[1]
                                                  }
                              })
        # object.__setattr__(self, "map", self.plot_map())

    def plot_map(self):
        """
        plot map with the sites location
        """

        index_lat, = np.where(self.columns == "latitude")[0]
        index_lon, = np.where(self.columns == "longitude")[0]

        latitudes = self._get_column_array(index_lat)
        longitudes = self._get_column_array(index_lon)

        center = [np.mean([np.min(latitudes), np.max(latitudes)]),
                  np.mean([np.min(longitudes), np.max(longitudes)])]

        mapa = folium.Map(location=center, zoom_start=3)
        folium.LayerControl().add_to(mapa)

        for i in self.index:
            popup = ("<strong>Name:</strong> %s<br>"
                     % (self._get_value(i, "name")) +
                     "<strong>Distance:</strong> %.2f"
                     % (self._get_value(i, "distance")))

            folium.Marker([self._get_value(i, "latitude"),
                           self._get_value(i, "longitude")],
                          popup=folium.Popup(popup, max_width=480),
                          tooltip="Click me!").add_to(mapa)

        folium.Marker([self.metadata["Reference Point"]["latitude"],
                       self.metadata["Reference Point"]["longitude"]],
                      icon=folium.Icon(color="red"),
                      popup=folium.Popup("Reference Point", max_width=480),
                      tooltip="Click me!").add_to(mapa)

        return mapa
