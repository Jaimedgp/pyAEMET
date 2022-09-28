SITES_TRANSLATION = {
    "site": {"id": "indicativo",
             "dtype": "string"},
    "name": {"id": "nombre",
             "dtype": "string"},
    "synindic": {"id": "indsinop",
                 "dtype": "string"},
    "latitude": {"id": "latitud",
                 "dtype": "float64"},
    "longitude": {"id": "longitud",
                  "dtype": "float64"},
    "altitude": {"id": "altitud",
                 "dtype": "float64"},
    "district": {"id": "distrito",
                 "dtype": "string"},
    "city": {"id": "ciudad",
             "dtype": "string"},
    "subregion": {"id": "provincia",
                  "dtype": "string"},
    "region": {"id": "Comunidad Autonoma",
               "dtype": "string"},
    "subregion_aemet": {"id": "provincia",
                        "dtype": "string"},
}


OBSERVATIONS_TRANSLATION = {
    "date": {"id": "fecha",
             "dtype": "datetime64"},
    "site": {"id": "indicativo",
             "dtype": "string"},
    "altitude": {"id": "altitud",
                 "dtype": "float64"},
    "temp_avg": {"id": "tmed",
                 "dtype": "float64"},
    "precipitation": {"id": "prec",
                      "dtype": "float64"},
    "temp_min": {"id": "tmin",
                 "dtype": "float64"},
    "temp_max": {"id": "tmax",
                 "dtype": "float64"},
    "hr_temp_min": {"id": "horatmin",
                    "dtype": "object"},
    "hr_temp_max": {"id": "horatmax",
                    "dtype": "object"},
    "wnd_dir": {"id": "dir",
                "dtype": "float64"},
    "wnd_spd": {"id": "velmedia",
                "dtype": "float64"},
    "wnd_gst": {"id": "racha",
                "dtype": "float64"},
    "hr_wnd_gst": {"id": "horaracha",
                   "dtype": "object"},
    "press_max": {"id": "presMax",
                  "dtype": "float64"},
    "hr_press_max": {"id": "horaPresMax",
                     "dtype": "object"},
    "press_min": {"id": "presMin",
                  "dtype": "float64"},
    "hr_press_min": {"id": "horaPresMin",
                     "dtype": "object"},
    "hr_sun": {"id": "sol",
               "dtype": "float64"},
}

V1_TRANSLATION = {
    "site": "indicativo",
    "name": "nombre",
    "synindic": "indsinop",
    "latitude": "latitud",
    "longitude": "longitud",
    "altitude": "altitud",
    "district": "distrito",
    "city": "ciudad",
    "subregion": "provincia",
    "region": "CA",
    "subregion_aemet": "provinciaAemet",
    "distance": "distancia",
}

