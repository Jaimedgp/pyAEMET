"""
ObservationsDataFrame
-----------------

"""

from pandas import DataFrame

# import numpy as np


class ObservationsDataFrame(DataFrame):
    """
    NEEDS TO HAVE THE FOLLOWING COLUMNS:

        site (CODE)
        date (DATE/DATETIME OF THE OBSERVATION)

    THE VARIABLES MUST BE PASS AS COLUMNS

    """

    def __init__(
            self,
            data=None,
            index=None,
            columns=None,
            dtype=None,
            copy=None,
            library: str=None,
            metadata: dict=None,
    ):

        super().__init__(
            data=data,
            index=index,
            columns=columns,
            dtype=dtype,
            copy=copy
        )

        if metadata is None:
            metadata = {}
        object.__setattr__(self, "library", library)
        object.__setattr__(self, "metadata", metadata)
