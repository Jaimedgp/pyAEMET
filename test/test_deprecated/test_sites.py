import pytest
from pandas import DataFrame

from .. import clima


@pytest.mark.parametrize("sites, codes", [
    ({"ciudad": ["Santander"]}, "1111X"),
    ({"ciudad": ["Santander"]}, "1111X"),
    ({"ciudad": ["Santander"]}, "1111X"),
    ({"ciudad": ["Santander"]}, "1111X"),
    ({"ciudad": ["Santander"]}, "1111X"),
    ])
def test_sites_in(sites, codes):

    response = clima.estaciones_loc(**sites, actualizar=False)

    assert isinstance(response, DataFrame)
    assert codes in response.indicativo.values
    assert response.shape == (3, 11)


def test_sites():

    response = clima.estaciones_info(actualizar=True)
    assert isinstance(response, DataFrame)
    assert not response.empty


def test_sites_near():
    response = clima.estaciones_cerca(latitud=43.47,
                                      longitud=-3.798,
                                      n_cercanas=4,
                                      actualizar=False,
                                      )

    print(type(response))
    assert isinstance(response, DataFrame)
