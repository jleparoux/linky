import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yaml
from dateutil import relativedelta
from src.utils import json_to_dataframe

from .paths import RAW_DATA_DIR


def transform_raw_data_into_ts_data(
    jsons: dict,
    data_type: str="hourly",
    exclude_data: tuple=("interval_length", "measure_type"),
) -> pd.DataFrame:
    """ """

    # parameters
    if data_type not in ("hourly", "daily"):
        raise ValueError("data_type value must be in the following list : hourly, daily")
    if data_type == "hourly":
        date_format = "%Y-%m-%d %H:%M:%S"
        missing_data_frequency = "H"
        resample = "60min"
    if data_type == "daily":
        date_format = "%Y-%m-%d"
        missing_data_frequency = "D"
        resample = None

    # convert all json data to pandas DataFrame
    if len(jsons) > 1:
        dfs = []
        for i, json in enumerate(jsons):
            # print(json)
            # transform json to pd.DataFrame
            try:
                jsondata = json['meter_reading']['interval_reading']
                dfs.append(json_to_dataframe(jsondata, date_format=date_format))
            except Exception as e:
                print(f" unable to transform the json {i} to df.")

        # concat all dfs to only one
        df = pd.concat(dfs)
    else:
        jsondata = jsons['meter_reading']['interval_reading']
        df = json_to_dataframe(jsondata, date_format=date_format)

    # force data type as float for value and replace column name
    df = df.rename(columns={'value': 'consumption'})
    df['consumption'] = df['consumption'].astype('float64')
    # df.drop(['value'], axis=1, inplace=True)

    # exlude data from columns if needed
    df = df.loc[ : , ~df.columns.isin(exclude_data)]

    # sorting by date
    df.sort_values(by=['date'], inplace=True)
    
    # resampling data hourly
    if resample is not None:
        df = df.resample(resample).mean()
        df = df.groupby([df.index]).sum().reset_index()
        df = df.set_index('date', drop=True)
        df.index = df.index.floor('H')

    # drop nan values and reindex
    # df.dropna(inplace=True)
    df = add_missing_date(df, frequency=missing_data_frequency)
    
    # # compute features engineering data
    df['day'] = df.index.day_name()
    df['month'] = df.index.month_name()
    df['year'] = df.index.year.astype('int64')

    if data_type == "hourly":
        df['hour'] = df.index.hour + df.index.minute/60 + df.index.second/3600
        df['daytime'] = compute_daytime(df)
        df['price'] = df['consumption'] * 0.09 / 1000   

    return df


def compute_daytime(
    df: pd.DataFrame
) -> pd.Series:
    '''
    Identidy period of the day based on hour (datetime)

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame

    Returns
    -------
    df['daytime'] : pd.Series
    '''

    df['daytime'] = np.nan

    df['daytime'] = np.where((df.index.hour>=0) & (df.index.hour<=6), 'night', df['daytime'])
    df['daytime'] = np.where((df.index.hour>6) & (df.index.hour<11), 'morning', df['daytime'])
    df['daytime'] = np.where((df.index.hour>=11) & (df.index.hour<14), 'midday', df['daytime'])
    df['daytime'] = np.where((df.index.hour>=14) & (df.index.hour<18), 'afternoon', df['daytime'])
    df['daytime'] = np.where((df.index.hour>=18) & (df.index.hour<=23), 'evening', df['daytime'])
    
    return df['daytime']


def add_missing_date(
    ts_data: pd.DataFrame,
    frequency: str="H"
) -> pd.DataFrame:
    """ """
    
    # initialization
    output = pd.DataFrame()

    # duplicate date index as column
    ts_data["date"] = ts_data.index

    full_range = pd.date_range(ts_data["date"].min(),
                               ts_data["date"].max(),
                               freq=frequency)

    # quick way to add missing dates with 0 in a Series
    output.index = pd.DatetimeIndex(ts_data.index)
    output = ts_data.reindex(full_range, fill_value=0)

    # drop date column
    output.drop(['date'], axis=1, inplace=True)
    
    return output