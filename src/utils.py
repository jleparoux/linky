import json
from pathlib import Path

import pandas as pd


def write_json_file(
    jsonfile: str, 
    data: dict
) -> None:
    ''' 
    Function to write json file with response data

    Parameters
    ----------
    jsonfile : str
    data : dict

    Returns
    -------
    None
    '''

    with open(jsonfile, 'w') as f:
        json.dump(data, f)
        print(f" json file sucessfully written: {Path(jsonfile).absolute()}")
    

def json_to_dataframe(
    jsondata: dict,
    date_format: str = '%Y-%m-%d %H:%M:%S'
) -> pd.DataFrame:
    '''
    Transorm json data to a pandas DataFrame

    Parameters
    ----------
    jsondata : dict
        data in json format from enedis api

    Returns
    -------
    df : pd.DataFrame
        a DataFrame containing json data
    '''

    df = pd.DataFrame(jsondata)

    if "date" in df.columns:
        df['date'] = pd.to_datetime(df['date'], format=date_format)
        df = df.set_index('date', drop=True)
        df.index = df.index + pd.DateOffset(seconds=-1)

    return df