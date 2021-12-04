"""
            AEMET API MODULE

    Python module to operate with AEMET OpenData API

    @author Jaimedgp
"""

import re
import time
import requests


class _AemetApiUse():
    """ Class to download climatological data using AEMET api"""

    def __init__(self, apikey):
        """ Get the needed API key"""

        self.main_url = "https://opendata.aemet.es/opendata"
        self._param = {"api_key": apikey}
        self._headers = {"cache-control": "no-cache",
                         "Accept": "application/json",
                         "Content-Type": "application/json",
                         }

    def request_info(self, url):
        """ Docstring """

        response = requests.request("GET",
                                    self.main_url + url,
                                    headers=self._headers,
                                    params=self._param
                                    )

        if response.ok:
            while response.json()["estado"] == 429:
                time.sleep(50)
                response = requests.request("GET",
                                            self.main_url + url,
                                            headers=self._headers,
                                            params=self._param
                                            )

            if response.json()["estado"] == 200:
                return self._request_data(response.json())
            if response.json()["estado"] == 404:
                return {}, {}
            if response.json()["estado"] == 401:
                return {}, {}

            return response.json(), {}

        return {}, {}

    def _request_data(self, response_dict):
        """ Docstring """

        response = requests.request("GET",
                                    response_dict["datos"],
                                    headers=self._headers,
                                    params=None)

        metadata = requests.request("GET",
                                    response_dict["metadatos"],
                                    headers=self._headers,
                                    params=None)

        if response.ok:
            return response.json(), metadata.json()

        return dict


def _transform_data(dictionary):
    """ Docstring """

    _decimal_notation = re.compile(r'(?<=\d),(?=\d)')

    # change decimal notation '0,0' => '0.0'
    return _decimal_notation.sub(".", dictionary)
