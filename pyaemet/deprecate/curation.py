"""
                Meteorology Curation

 Do stuff

 @author Jaimedgp

"""


import os

import pandas as pd


def get_proportion_info(data_AEMET, stdy_prd):
    """ Calculate the proportion of data of each variable in data_AEMET for the
        given study period of time

        @params:
            data_AEMET: pandas DataFrame with meteo data
            stdy_prd: list with start and end dates of study.
                      e.g.: [start_dt, end_dt]
        @return:
            pandas DataFrame row with relevant information of data_AEMET.
                - site: data_AEMET AEMET station code
                - start_dt: date of beginning of data collection
                - end_dt: date of end of data collection
                - miss.dy: number of missing days respect study period

                * variable: proportion of available data respect study
                            period
    """

    # period => [start_dt, end_dt] == (start_dt, end_dt)+2
    period = (stdy_prd[1] - stdy_prd[0]).days + 2

    general_info = pd.DataFrame({"site": data_AEMET["indicativo"].unique(),
                                 "start_dt": min(data_AEMET["fecha"]),
                                 "end_dt": max(data_AEMET["fecha"]),
                                 "miss_dy": period - len(data_AEMET.index)
                                 })

    amount_df = (data_AEMET.notna().sum() / period).to_frame().T

    return pd.concat([general_info, amount_df], axis=1)


def is_enough_data(proportion_info, min_prop):
    """
        Define if proportion_info is enough to study.

        @params:
            proportion_info: pandas DataFrame from get_proportion_info function
            min_prop: minimum proportion of data to consider enough data in
                      main study period.
                           valid_values
                       ------------------  > minPercentage
                           Total_values
        @return:
            Boolean if proportion of data is enough to study

    """

    return (proportion_info.iloc[:, 4:] > min_prop).all(axis=1)[0]


def download_nearest_data(aemet, siteAQ, stdy_prd, remove_cl, selected_cl,
                          folder, n=3, min_prop=0.8):
    """
        Download AEMET meteo data from the nearest station to the air
        quality station. If data is available, it is saved.

        @params:
            Aemet: DownloadAEMET object for AEMET API interaction
            siteAQ: Pandas DataFrame row with AQ station information.
                    Should have 'latitude', 'longitude' and 'site' columns
            study_prd: list with start and end dates of study.
                       e.g.: [start_dt, end_dt]
            removed_cl: Columns names that should be removed for the study
            removed_cl: Columns names that should be selected for the study
            folder: Folder path where files are saved

            n: Number of nearest stations to try to download. Default: 3
            min_prop: minimum proportion of data to consider enough data in
                      curation function. Default: 0.8 # 80%
        @return:
            pandas DataFrame with station data available among the nearest
            n stations
    """

    n_station = aemet.get_nearest_stations(lat=siteAQ["latitude"],
                                           long=siteAQ["longitude"],
                                           n=n)
    n_station["siteAQ"] = siteAQ["site"]

    for i, st in enumerate(n_station["indicativo"].values):
        if os.path.isfile(folder+st+".csv"):
            station = n_station.iloc[i].to_frame().T
            break

        all_data = aemet.get_data(dates=stdy_prd,
                                  station_id=st,
                                  )

        if all_data is not None:
            min_names = [nm for nm in all_data.columns
                         if nm in selected_cl]
            if len(min_names) == len(selected_cl):
                names = [nm for nm in all_data.columns
                        if nm not in remove_cl]

                prop_info = get_proportion_info(all_data[names], stdy_prd)

                if is_enough_data(prop_info, min_prop):
                    all_data.to_csv(folder+st+".csv", index=False)

                    station = n_station.iloc[i].to_frame().T
                    break
    else:
        print("No data enough in any of the nearest n stations")
        station = None

    return station
