from datetime import date
import pytest

from src.pyaemet.types_classes.sites import (
    SitesDataFrame,
    NearSitesDataFrame
    )

from . import clima


@pytest.mark.parametrize("sites, codes", [
    ({"city": ["Santander"]}, "1111X"),
    ({"city": ["Santander"]}, "1111X"),
    ({"city": ["Santander"]}, "1111X"),
    ({"city": ["Santander"]}, "1111X"),
    ({"city": ["Santander"]}, "1111X"),
    ])
def test_sites_in(sites, codes):

    response = clima.sites_in(**sites, update_first=False)

    assert isinstance(response, SitesDataFrame)
    assert codes in response.site.values
    assert response.shape == (3, 11)


def test_sites():

    response = clima.sites_info(update=True)

    assert isinstance(response, SitesDataFrame)


def test_sites_near():
    response = clima.near_sites(latitude=43.47,
                                longitude=-3.798,
                                n_near=4,
                                update_first = False,
                                )

    assert isinstance(response, NearSitesDataFrame)


def test_curation():
    sites = clima.near_sites(latitude=43.47,
                             longitude=-3.798,
                             n_near=4,
                             update_first = False,
                             )
    response = clima.sites_curation(
        start_dt=date.today(),
        end_dt=date.today(),
        sites=sites,
        threshold=0.75,
        variables='all',
        save_folder=None,
        )

    assert isinstance(response, SitesDataFrame)
