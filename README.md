# pyAEMET

pyaemet es una librería para python desarrollada para la descarga de los valores
climatologicos diarios de la AEMET a partir de su API OpenData. La librería
contiene una serie de métodos que facilitan la descarga y filtrado de los datos
climatológicos y cuyo uso se detalla a continuacion.

## Installation

``` bash

$ pip install pyAEMET-Jaimedgp

```


## Uso de la librería
Para poder usar la librería es necesario disponer de una APIkey de OpenData
AEMET que se puede obtener en este
[link](https://opendata.aemet.es/centrodedescargas/obtencionAPIKey). A partir de
esta clave se puede crear un objeto de la clase principal `AemetClima` que
permitirá utilizar los métodos de la librería.

Se puede consultar el ipython notebook `doc/ejemplo-uso.ipnb` con ejemplos de uso.

```python
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

Por otro lado, el método `AemetClima.estaciones_cerca()` te permite obtener las `n_cercanas`
estaciones de la AEMET más cercanas a una cierta localización definida por sus coordenadas
latitud y longitud, junto con su distancia a la localización en km. Por defecto se devuelven
las 3 estaciones más cercanas.

```python
AemetClima(apikey).estaciones_cerca(latitud, longitud, n_cercanas=3)
```

Por otro lado, se ha añadido el método `AemetClima.estaciones_curacion` para facilitar el
curado de los datos. Este método permite obtener las estaciones que cumplan el requisito de
que tengan al menos un porcentaje determinado `umbral` de los datos de ciertas variables
`variables` disponibles. El método puede comportarse de dos maneras distintas en función de
los argumentos que se le pasen.

El método `AemetClima.estaciones_curacion` permite pasarle la información de las estaciones
de las cuales se quiere obtener información sobre la cantidad de datos disponibles. De esta
forma, si se le pase el argumento `estaciones` mediante su `indicativo` en forma de `string`
o lista de `strings` o pasando directamente un pandas.DataFrame devuelto por los métodos
vistos anteriormente con la información de las estaciones el método añadirá la columna
`suficientesDatos` booleana según si la estación cumple o no la condición.

```python
AemetClima(apikey).estaciones_curacion(estacion,
                                       fecha_ini=datetime.date(),
                                       fecha_fin=datetime.date.now(),
                                       umbral=0.75,  # por defecto se toma el 75%
                                       variables=columnas,
                                       save_folder="directorio/guardar/los/datos/")
```

Por otro lado, se puede utilizar esta funcion para obtener la estación más cercana a una
localización que cumpla el requisito de los datos mínimos. Esta función obtiene la
información de las estaciones llamando a la función
`AemetClima.estaciones_cerca(latitud, longitud, n_cercanas)`.

```python
AemetClima(apikey).estaciones_curacion(latitud, longitud, n_cercanas,
                                       fecha_ini=datetime.date(),
                                       fecha_fin=datetime.date.now(),
                                       umbral=0.75,  # por defecto se toma el 75%
                                       variables=columnas,
                                       save_folder="directorio/guardar/los/datos/")
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

## Referencias
La información que recoge y utiliza esta librería es propiedad de la Agencia
Estatal de Meteorología disponible mediante su API REST [AEMET
OpenData](https://opendata.aemet.es/centrodedescargas/AEMETApi?).
