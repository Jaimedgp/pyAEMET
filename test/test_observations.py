from datetime import date
import pytest

from src.pyaemet.types_classes.observations import ObservationsDataFrame

from . import clima


@pytest.mark.parametrize("site, dates", [
    ("1111X", [date(2020, 1, 1), date(2020, 2, 1)]),
    ("3100B", [date(2020, 1, 1), date(2020, 2, 1)]),
    ("1111X", [date(2020, 1, 1), date(2020, 2, 1)]),
    ("3100B", [date(2020, 1, 1), date(2020, 2, 1)]),
    ("1111X", [date(2020, 1, 1), date(2020, 2, 1)]),
    ])
def test_daily_clima(site, dates):

    response = clima.daily_clima(site=site,
                                 start_dt=dates[0],
                                 end_dt=dates[1])

    assert isinstance(response, ObservationsDataFrame)
    assert not response.empty
    assert response.site.values == site
    assert response.shape[0] == 32
