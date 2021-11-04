# pyAEMET
---

pyaemet es una librería para python desarrollada para la descarga de los valores
climatologicos diarios de la AEMET a partir de su API OpenData. La librería
contiene una serie de métodos que facilitan la descarga y filtrado de los datos
climatológicos y cuyo uso se detalla a continuacion.

## Installation

``` bash

$ pip install ./

```


## Uso de la librería
---
Para poder usar la librería es necesario disponer de una APIkey de OpenData
AEMET que se puede obtener en este
[link](https://opendata.aemet.es/centrodedescargas/obtencionAPIKey). A partir de
esta clave se puede crear un objeto de la clase principal `AemetClima` que
permitirá utilizar los métodos de la librería.

```python
from pyaemet.apikey_file import apikey
from pyaemet.valores_climatologicos import AemetClima

aemet = AemetClima(apikey=apikey)
```

### Información de las estaciones

La librería permite obtener información sobre las estaciones con datos
climatológicos diarios disponibles por la AEMET. Además de la información de
cada estación facilitada por la AEMET también se incluyen el Distrito, Ciudad,
Provincia y Comunidad Autónoma de cada estación.

Para algunos casos se ha detectado que la provincia facilitada no corresponde
con la provincia obtenida a partir de las coordenadas debido a que la estación
se encuentra proxima a los límites entre provincias. Por ello se ha denominado
la provincia facilitada por la AEMET con el nombre de `provinciaAemet` y la
determinada por las coordenadas como `provincia`.

```python
AemetClima(apikey).estaciones_info()
```

Para facilitar el filtrado de las estaciones se ha incluido el método
`AemetClima.estaciones_loc()` que permite filtrar las estaciones por los valores
sus columnas. De esta manera se pueden filtrar las estaciones por ciudad,
provincia o comunidad autónoma.

```python
    AemetClima(apikey).estaciones_loc(nombre_columna=["lista de valores"])
```

```{.python .input  n=18}
# estaciones disponibles en la provincia de Barcelona
pontevedra = aemet.estaciones_loc(provincia=["Pontevedra"])
```

```{.python .input  n=6}
# Estaciones disponibles en la comunidad de Madrid
madrid = aemet.estaciones_loc(CA=["Comunidad de Madrid"])
madrid.head()
```

Por otro lado, el método `AemetClima.estaciones_cerca(latitud, longitud,
n_cercanas)` te permite obtener las `n_cercanas` estaciones de la AEMET más
cercanas a una cierta localización definida por sus coordenadas latitud y
longitud, junto con su distancia a la localización en km. Por defecto se
devuelven las 3 estaciones más cercanas.

```{.python .input  n=8}
cerca = aemet.estaciones_cerca(latitud=43.47, longitud=-3.798, n_cercanas=5)
cerca.head()
```

### Descarga Valores Climatológicos

Para la descarga de los datos climatológicos se han de pasar las fechas de
inicio y final de los datos, que han de ser objetos de la clase `datetime.date`
o `datetime.datetime` y las estaciones de las cuales se quieren obtener los
datos. Estas últimas se pueden pasar mediante su `indicativo` en forma de
`string` o lista de `strings` o pasando directamente un pandas.DataFrame
devuelto por los métodos vistos anteriormente con la información de las
estaciones. El valor de la fecha de fin por defecto será la del día en el que se
encuentre `datetime.date.today()`.

```python
AemetClima(apikey).clima_diaria(estacion,
                                fecha_ini=datetime.date(),
                                fecha_fin=datetime.date.today()
                                )
```

```{.python .input  n=11}
from datetime import date

data_aranjuez = aemet.clima_diaria(estacion="3100B",
                                   fecha_ini=date(2015, 1, 1),
                                   fecha_fin=date(2021, 5, 1)
                                   )
data_aranjuez.head()
```

```{.python .input  n=16}
# Datos de la provincia de Tarragona
# Se pasa el pandas.DataFrame obtenido anteriormente
data_pontevedra = aemet.clima_diaria(estacion=pontevedra,
                                    fecha_ini=date(2015, 1, 1),
                                    fecha_fin=date(2021, 5, 1)
                                    )
```

```{.python .input  n=17}
data_pontevedra.groupby("indicativo").plot(x="fecha", y="tmin")
```

## Referencias
---
La información que recoge y utiliza esta librería es propiedad de la Agencia
Estatal de Meteorología disponible mediante su API REST [AEMET
OpenData](https://opendata.aemet.es/centrodedescargas/AEMETApi?).
