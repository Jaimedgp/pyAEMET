"""
Data Curation
---------------

:author Jaimedgp
"""

import re
from datetime import time
from pandas import Series, isna, DataFrame


def update_fields(data, metadata, new_metadata):
    """
    """

    for k, v in new_metadata.items():
        if k in data.columns:
            for i in metadata:
                if i["id"] == v["id"].lower():
                    v["aemet"] = {k: v for k, v in i.items() if k != "id"}
                    break

    return new_metadata


def _str_decima_notation(value):
    """ Docstring """

    if isna(value):
        return value

    # change decimal notation '0,0' => '0.0'
    return re.compile(r'(?<=\d),(?=\d)').sub(".", value)


def decimal_notation(column: Series):
    """ Docstring """

    if column.name not in ["date", "site"]:
        column = column.apply(_str_decima_notation)

    return column


def hr_to_datetime(value):
    """ Docstring """

    if isna(value):
        pass
    elif isinstance(value, str):
        if value == "-1":
            value = time(0, 0, 59)
        elif value == "24":
            value = time(hour=0,
                         minute=0,
                         second=0)
        elif ":" in value:
            hour, minute = value.split(":")
            value = time(hour=int(hour),
                         minute=int(minute),
                         second=0)
        else:
            value = time(hour=int(value),
                         minute=0,
                         second=0)

    return value


def convert_hours(column: Series):
    """ Docstring """

    if column.name.startswith("hr_"):
        column = column.apply(hr_to_datetime)

    return column


def remove_newline(data: DataFrame):

    return data.replace(r'\n', '', regex=True)
