# pyAEMET


[![PyPI Latest Release](https://img.shields.io/pypi/v/pyaemet.svg)](https://pypi.org/project/pyaemet/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5655307.svg)](https://doi.org/10.5281/zenodo.5655307)
[![License](https://img.shields.io/pypi/l/pandas.svg)](https://github.com/jaimedgp/pyAEMET/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/personalized-badge/pyaemet?period=month&units=international_system&left_color=gray&right_color=orange&left_text=PyPI%20downloads%20per%20month)](https://pepy.tech/project/pyaemet)

A python library developed to download daily climatological values from the Spanish National
Meteorological Agency (AEMET) through its OpenData API. The library contains several methods
to facilitate downloading and filtering the climatological data.

> The information that this library collects and uses is property of the Spanish State
> Meteorological Agency, available through its AEMET OpenData REST API.


## Installation
``` bash
$ pip install pyaemet
```
To use the pyAEMET module, you need to get an API key from the AEMET (Spanish State Meteorological
Agency) OpenData platform. You can apply for a key [here](https://opendata.aemet.es/centrodedescargas/altaUsuario).

## Usage

Once the module is installed and you have your API key, you can start using the module by
importing it in your Python script. To use the module's functions, you need to initialize
the client with your API key:

```python
import pyaemet

aemet = pyaemet.AemetClima(api_key)
```

The `AemetClima` class takes an API key as a parameter in its constructor and allows you to get
information about the available monitoring sites, filter sites based on different parameters
(e.g., city, province, autonomous community), and get nearby sites to a specific location.

Here is a summary of some of the methods provided by the `AemetClima` class:

* **`sites_info`**: Retrieves information about all the available monitoring sites. The method
returns an instance of the `SitesDataFrame` class, which is a subclass of the pandas `DataFrame`.
```python
aemet.sites_info(update=True)
```

* **`sites_in`**: Filters the available monitoring sites based on specified parameters
(e.g., city, province, autonomous community). The method returns an instance of the `SitesDataFrame` class.
```python
aemet.sites_in(subregion="Cantabria")
```
![image](https://github.com/Jaimedgp/pyAEMET/raw/main/docs/screenshots/sites_cantabria.png)

* **`near_sites`**: Retrieves the ``n_near`` monitoring sites closest to a specified latitude and longitude,
within a maximum distance of `max_distance` kilometers. The method returns an instance of the
`NearSitesDataFrame` class.
```python
aemet.near_sites(latitude=43.47,
                 longitude=-3.798,
                 n_near=5, max_distance=50)
```
![image](https://github.com/Jaimedgp/pyAEMET/raw/main/docs/screenshots/near_sites.png)

* **`sites_curation`**: Retrieves the amount of available data of certain `variables` in the monitoring `sites` in a period of time defined by
    `start_dt` and `end_dt`. The function returns a `SitesDataFrame` or `NearSitesDataFrame` (depends of the type of the `sites` parameter given)
    with a column with the average `amount` between all `variables` and `has_enough` boolean if the amount is greater or equal to a `threshold`.

* **`daily_clima`**: Retrieves daily climate data for a given ``site`` or a list of sites over a
specified date range defined by `start_dt` and `end_dt`. The function returns a
`ObservationsDataFrame` object, which is a data structure that holds the retrieved climate data
along with any associated metadata.
```python
import datetime
aemet.daily_clima(site=aemet.sites_in(city="Santander"),
                  start_dt=datetime.date(2022, 6, 3),
                  end_dt=datetime.date.today())
```

The module also provides three deprecated methods `estaciones_info`, `estaciones_loc` and `clima_diaria`
that perform similar functionality as the `sites_info`, `sites_in` and `daily_clima` methods, respectively.

You can find the complete documentation of the module's functions in the GitHub repository,
under the docs directory.

## FAQ
## Contributing
## References
* ["Estimating changes in air pollutant levels due to COVID-19 lockdown measures based on a business-as-usual prediction scenario using data mining models: A case-study for urban traffic sites in Spain"](https://doi.org/10.1016/j.scitotenv.2022.153786), submitted to Environmental Software & Modelling by [J. González-Pardo](https://orcid.org/0000-0001-7268-9933) et al. (2021)
