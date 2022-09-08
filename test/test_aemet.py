import os

import pytest

import pyaemet as pae
from pyaemet.types_classes.sites import (
    SitesDataFrame,
    NearSitesDataFrame
    )


def test_version():
    assert pae.__version__ == "2.0.1"


clima = pae.AemetClima(apikey=os.getenv("SECRET_KEY"))


@pytest.mark.parametrize("sites, codes", [
    ( { "city": ["Santander"] }, "1111X" ),
    ( { "city": ["Santander"] }, "1111X" ),
    ( { "city": ["Santander"] }, "1111X" ),
    ( { "city": ["Santander"] }, "1111X" ),
    ( { "city": ["Santander"] }, "1111X" ),
    ])
def test_sites_in(sites, codes):

    response = clima.sites_in(**sites, update_first=False)
    print(response.head())

    assert isinstance(response, SitesDataFrame)
    assert codes in response.site.values
    assert response.shape == (3, 11)


def test_sites():

    assert isinstance(clima.sites_info(update=False), SitesDataFrame)


def test_sites_near():
    assert isinstance(clima.near_sites(latitude=43.47,
                                       longitude=-3.798,
                                       n_near=4,
                                       update_first = False,
                                       ),
                      NearSitesDataFrame)


def test_daily_clima():
    assert True
