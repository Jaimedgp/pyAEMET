"""
SitesDataFrame
-----------------

"""

import os
import json
from typing import List, Optional

import pandas
import folium
import numpy as np


class SitesDataFrame(pandas.DataFrame):
    """
    NEEDS TO HAVE THE FOLLOWING COLUMNS:

        site (CODE),
        name (NAME OF THE STATION),
        latitude,
        longitude
    """

    # pandas: disable=W0223

    def __init__(
            self,
            data=None,
            index=None,
            columns=None,
            dtype=None,
            copy=None,
            library: Optional[str] = None,
            metadata: Optional[dict] = None,
    ):

        super().__init__(
            data=data,
            index=index,
            columns=columns,
            dtype=dtype,
            copy=copy
        )

        self._validate(self)

        if metadata is None:
            metadata = {}
        object.__setattr__(self, "library", library)
        object.__setattr__(self, "metadata", metadata)

    @staticmethod
    def _validate(obj):
        """
        NEEDS TO HAVE THE FOLLOWING COLUMNS:

            site (CODE),
            name (NAME OF THE STATION),
            latitude,
            longitude
        """

        # verify there is a column latitude and a column longitude
        if "latitude" not in obj.columns or "longitude" not in obj.columns:
            raise AttributeError("Must have 'latitude' and 'longitude'.")
        # verify there is a column site and a column name
        if "site" not in obj.columns or "name" not in obj.columns:
            raise AttributeError("Each site must be identify by a code 'site'"
                                 + " and its name 'name'.")

    @staticmethod
    def open_from(
            data_fl: Optional[str] = None,
            metadata_fl: Optional[str] = None,
            folder_name: Optional[str] = None
    ):
        """
        """

        if data_fl is None:
            if folder_name is None:
                raise KeyError("Not correct file path")
            data_fl = folder_name + "data.pkl"
        if metadata_fl is None:
            if folder_name is None:
                raise KeyError("Not correct file path")
            metadata_fl = folder_name + "metadata.json"

        metadata = json.load(metadata_fl)

        return SitesDataFrame(
            data=pandas.read_csv(data_fl),
            library="pyaemet",
            metadata=metadata
            )

    def save(self, folder_name: str, extension: str = 'pickle'):
        """
        """

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        if extension == 'pickle':
            self.to_pickle(folder_name+"data.pkl")
        elif extension == 'csv':
            self.to_csv(folder_name+"data.csv")

        with open(folder_name+"metadata.json", 'w') as file:
            json.dump(self.metadata, file, indent=4)

    def copy(self, deep=True):
        """ Copy object """

        return SitesDataFrame(data=super().copy(deep),
                              library=self.library,
                              metadata=self.metadata)

    def as_dataframe(self):
        return super().copy(True)

    @property
    def map(self):
        """
        plot map with the sites location
        """

        if self.empty:
            return folium.Map()

        index_lat, = np.where(self.columns == "latitude")[0]
        index_lon, = np.where(self.columns == "longitude")[0]

        latitudes = self._get_column_array(index_lat)
        longitudes = self._get_column_array(index_lon)

        center = [np.mean([np.min(latitudes), np.max(latitudes)]),
                  np.mean([np.min(longitudes), np.max(longitudes)])]

        mapa = folium.Map(location=center, zoom_start=3)

        for i in self.index:
            popup = ("<strong>Site:</strong> %s<br>"
                     % (self._get_value(i, "site")) +
                     "<strong>Name:</strong> %s"
                     % (self._get_value(i, "name")))
            folium.Marker([self._get_value(i, "latitude"),
                           self._get_value(i, "longitude")],
                          popup=folium.Popup(popup, max_width=480),
                          tooltip="Click me!").add_to(mapa)

        return mapa

    def filter_in(self, **kwargs):
        """
        """

        kwargs.update(
            {k: [v] for k, v in kwargs.items() if not isinstance(v, list)})

        if any(not isinstance(x, list) for x in kwargs.values()):
            raise(TypeError("only list-like objects are allowed to be passed" +
                            " to filter_in(), you passed a [str]"))
        if any(x not in self.columns for x in kwargs):
            raise(KeyError("The keys passed to filter_in() does not match " +
                           "with SitesDataFrame columns"))

        sites = super().copy()
        for ky, vl in kwargs.items():
            sites = sites.__getitem__(sites.__getitem__(ky).isin(vl))

        return SitesDataFrame(data=sites,
                              library=self.library,
                              metadata=self.metadata)

    def filter_at(
            self,
            latitude: float,
            longitude: float,
            n_near: int = 100,
            max_distance: float = 6237.0,
    ):
        """
        """

        sites_distance = self.calc_distance(latitude, longitude)

        sites_distance = sites_distance.__getitem__(
            sites_distance.__getitem__("distance") <=
            max_distance).sort_values(by=['distance'],
                                      ascending=True)[:(n_near)]

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

        coor1 = pandas.DataFrame(np.deg2rad(self.__getitem__(["latitude",
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
    MUST HAVE THE FOLLOWING COLUMNS:

        site (CODE),
        name (NAME OF THE STATION),
        latitude,
        longitude,
        distance (TO THE REFERENCE POINT)
    """

    def __init__(
            self,
            ref_point: List[float],
            data=None,
            index=None,
            columns=None,
            dtype=None,
            copy=None,
            library=None,
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
            library=library,
            metadata=metadata,
        )

        self.metadata.update({"Reference Point": {"latitude": ref_point[0],
                                                  "longitude": ref_point[1]
                                                  }
                              })

    @staticmethod
    def _validate(obj):
        """
        MUST HAVE THE FOLLOWING COLUMNS:

            site (CODE),
            name (NAME OF THE STATION),
            latitude,
            longitude
        """

        # verify there is a column latitude and a column longitude
        if "latitude" not in obj.columns or "longitude" not in obj.columns:
            raise AttributeError("Must have 'latitude' and 'longitude'.")
        # verify there is a column site and a column name
        if "site" not in obj.columns or "name" not in obj.columns:
            raise AttributeError("Each site must be identify by a code 'site'"
                                 + " and its name 'name'.")
        if "distance" not in obj.columns:
            raise AttributeError("NearSitesDataFrame must include the"
                                 + " 'distance' column")

    @property
    def map(self):
        """
        plot map with the sites location
        """

        if self.empty:
            return folium.Map()

        index_lat, = np.where(self.columns == "latitude")[0]
        index_lon, = np.where(self.columns == "longitude")[0]

        latitudes = self._get_column_array(index_lat)
        longitudes = self._get_column_array(index_lon)

        center = [np.mean([np.min(latitudes), np.max(latitudes)]),
                  np.mean([np.min(longitudes), np.max(longitudes)])]

        mapa = folium.Map(location=center, zoom_start=3)
        folium.LayerControl().add_to(mapa)

        for i in self.index:
            popup = ("<strong>Site:</strong> %s<br>"
                     % (self._get_value(i, "site")) +
                     "<strong>Name:</strong> %s<br>"
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

    def as_dataframe(self):
        return super().copy(True)

    def sort_values(self, **kwargs):
        return NearSitesDataFrame(
            data=super().sort_values(**kwargs),
            ref_point=[self.metadata["Reference Point"]["latitude"],
                       self.metadata["Reference Point"]["longitude"],
                       ],
            metadata=self.metadata
            )
