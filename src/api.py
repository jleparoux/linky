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

# linky package
from .paths import RAW_DATA_DIR
from .utils import write_json_file

# Global variables
AUTHORIZED_ENDPOINTS = ["consumption_load_curve", "daily_consumption", "daily_consumption_max_power"]

def __call_fake_enedis_api(
    api_tokens: dict,
    start: str,
    end: str,
    endpoint: str,
    jsonfile: str,
) -> requests.models.Response:
    """
    Function to call enedis api for daily consumption and return response containing

    Parameters
    ----------
    api_tokens : dict
    start : str
    end : str
    endpoint : str
    write_json : bool

    Returns
    -------
    response : requests.models.Response
    """
    # load json  file
    with open(jsonfile) as jsonf:
        response = json.load(jsonf)

    return response


def __call_enedis_api(
    api_tokens,
    start: str,
    end: str,
    endpoint: str,
    jsonfile: Path,
    write_json: bool=True,
) -> requests.models.Response:
    """
    Function to call enedis api for daily consumption and return response containing

    Parameters
    ----------
    api_tokens : dict
    start : str
    end : str
    endpoint : str
    write_json : bool

    Returns
    -------
    response : requests.models.Response
    """
    # params
    usage_point_id = api_tokens["usage_point_id"]
    user_access_token = api_tokens["access_token"]

    # API URL
    URL_API_ENEDIS = f"https://www.myelectricaldata.fr/{endpoint}/{usage_point_id}/start/{start}/end/{end}"

    # call api and get data
    my_headers = {'Authorization' : user_access_token, 'ContentType': 'application/json'}
    response = requests.get(URL_API_ENEDIS, headers = my_headers)
    
    # print error message if error is raised
    if response.status_code != 200:
        print(f" >>> Failed to get data with code error {response.status_code}: {response.json()}")
        return response

    #  write response to a json file
    if write_json:
        if not jsonfile.exists():
            write_json_file(jsonfile, response.json())
        else:
            print(f" >>> Json file {jsonfile} already exists. Nothing done.")

    return response


def _get_raw_daily_data(
    api_tokens: dict,
    endpoint: str,
    start: str,
    end: str,
    write_json: bool=True,
) -> dict:
    """ Get daily data from linky (36months history max)"""

    # initial check
    daily_endpoints = ("daily_consumption", "daily_consumption_max_power")
    if not endpoint.lower() in daily_endpoints:
        raise ValueError(f"ERROR: wrong value for endpoint. Authorized value: {daily_endpoints}")

    # params
    usage_point_id = api_tokens["usage_point_id"]

    # transform strftime to strptime
    from_date = datetime.strptime(start, '%Y-%m-%d')
    to_date = datetime.strptime(end, '%Y-%m-%d')

    # handle date error
    delta_date_timestamp = to_date.timestamp() - from_date.timestamp()
    if (delta_date_timestamp < 0):
        raise ValueError(" ERROR: the end date must be greater than the start date.")
    
    # check if start and end dates are greater than to 36months
    delta_date = relativedelta.relativedelta(to_date, from_date)
    delta_months = delta_date.months + (12*delta_date.years)
    start_date = start
    if (delta_months > 36):
        print(" WARNING: For daily data, the delta between end date and start date must be less than 36 months.")
        from_date = to_date - relativedelta.relativedelta(months=36) + timedelta(days=1)
        start_date = from_date.strftime("%Y-%m-%d")
        print(f"   start date has been updated to : {start_date}")

    # call api 
    print(f" >>  Endpoint : {endpoint}")
    print(f"   Load data from : {start_date} to {end}")

    jsonfile = RAW_DATA_DIR / f'{start_date}-{end}_{usage_point_id}_{endpoint}.json'

    # call fake api if json already exists
    if jsonfile.exists():
        response_ = __call_fake_enedis_api(api_tokens, start_date, end, endpoint, jsonfile=jsonfile)
        status_code = 200

    # if not, API is called
    else:
        # call api and get data
        response_ = __call_enedis_api(api_tokens, start_date, end, endpoint, jsonfile, write_json)
        status_code = response_.status_code
        response_ = response_.json()

    # append response
    if status_code == 200:
        response = response_

    return response


def _get_raw_load_curve(
    api_tokens: dict,
    endpoint: str,
    start: str,
    end: str,
    write_json: bool=True,
    max_api_call: int=50
) -> dict:
    """ Get load curve data from linky api (7days history per call)
    """

    # initial check
    load_curve_endpoints = ("consumption_load_curve")
    if not endpoint.lower() in load_curve_endpoints:
        raise ValueError(f"ERROR: wrong value for endpoint. Authorized value: {load_curve_endpoints}")
    
    # params
    usage_point_id = api_tokens["usage_point_id"]

    # transform strftime to strptime
    from_date = datetime.strptime(start, '%Y-%m-%d')
    to_date = datetime.strptime(end, '%Y-%m-%d')

    # handle date error
    delta_date_timestamp = to_date.timestamp() - from_date.timestamp()
    if (delta_date_timestamp < 0):
        raise ValueError(" ERROR: the end date must be greater than the start date.")
    
    # check if start and end dates are greater than to 7days
    delta_date = to_date - from_date
    if (delta_date.days > 7):
        print(" WARNING: For load curve data, the delta between end date and start date must be less than 7 days per call.")
    
    # recursive call to api rolling 7days (by week)
    response = []
    print(f" >>  Endpoint : {endpoint}")

    done = False
    current_date = to_date
    call_counter = 0
    while not done:
        current_date_weekday = current_date.weekday()
        current_date_start_delta = timedelta(days=current_date_weekday, weeks=0)
        last_begin_week_date = current_date - current_date_start_delta

        # datetime to str
        start_date = (last_begin_week_date - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = current_date.strftime("%Y-%m-%d")

        # call fake api if json already exists
        print(f" Load data from : {start_date} to {end_date}")
        jsonfile = RAW_DATA_DIR / f'{start_date}-{end_date}_{usage_point_id}_{endpoint}.json'
        if jsonfile.exists():
            response_ = __call_fake_enedis_api(api_tokens, start_date, end_date, endpoint, jsonfile=jsonfile)
            status_code = 200  # status code ok json file exists

        # if not, API is called
        else:
            # call api and get data
            response_ = __call_enedis_api(api_tokens, start_date, end_date, endpoint, jsonfile, write_json)
            status_code = response_.status_code
            response_ = response_.json()
            call_counter += 1

        # append response
        if status_code == 200:
            response.append(response_)

        # update current_date
        current_date = last_begin_week_date - timedelta(days=1)

        # stop after max_api_call number (to prevent over api calling)
        if ((call_counter >= max_api_call) 
        or ((last_begin_week_date - from_date).days < 0)
        or (status_code != 200)):
            done = True

    return response


def get_my_data_from_enedis_api(
    api_tokens: dict,
    endpoint: str,
    start: str,
    end: str="today",
    write_json: bool=True,
    max_api_call: int=50
    ):
    """ Get data from the enedis api and return response from requets
    """

    # setting parameters
    if end == "today":
        end = datetime.today().strftime('%Y-%m-%d')

    #  handle endpoint cases 
    if not endpoint.lower() in AUTHORIZED_ENDPOINTS:
        raise ValueError(f"The specified endpoint does not exist. Authorized endpoint : {AUTHORIZED_ENDPOINTS}")

    if endpoint.lower() == "consumption_load_curve":
        response = _get_raw_load_curve(api_tokens,
                                       endpoint.lower(),
                                       start,
                                       end,
                                       write_json=write_json,
                                       max_api_call=max_api_call)
        return response
    
    if endpoint.lower() == "daily_consumption":
        response = _get_raw_daily_data(api_tokens,
                                       endpoint.lower(),
                                       start,
                                       end,
                                       write_json=write_json)
        return response

    if endpoint.lower() == "daily_consumption_max_power":
        response = _get_raw_daily_data(api_tokens,
                                       endpoint.lower(),
                                       start,
                                       end,
                                       write_json=write_json)
        return response