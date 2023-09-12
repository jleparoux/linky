import json
from pathlib import Path
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
    
