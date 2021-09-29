import pyaemet.AEMET as aet
from pyaemet.apikey_file import apikey

def test_dist():

    assert aet(apikey).calc_dist(
                            [38.08472222, -0.85277777],
                            [38,          -1.167     ]) == 29.085047313828206


