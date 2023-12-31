import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

import yaml

PARAMETERS_PATH = os.path.dirname(os.path.abspath(__file__))
PARAMETERS_FILEPATH = Path(PARAMETERS_PATH) / 'parameters.yml'

@dataclass(slots=True)
class Configuration:
    """ Get the environment configuration from a Yaml file to set the user configuration
    """
    
    yaml_file: str = field(default=PARAMETERS_FILEPATH)
    settings: Dict = field(default_factory=dict)

    def __post_init__(self):
        """
        """

        # read user yaml parameters
        try:
            with open(self.yaml_file) as f:
                settings = yaml.safe_load(f)
        except Exception as e:
            raise(e)
        else:
            self.settings = settings

        # check required keys
        if not "api_enedis" in self.settings:
            print("in Configuration: key 'api_enedis' not found in user parameters.")
            sys.exit()
        
        if not "usage_point_id" in self.settings["api_enedis"]:
            print("in Configuration: key 'usage_point_id' not found in user parameters.")
            sys.exit()

        if not "access_token" in self.settings["api_enedis"]:
            print("in Configuration: key 'access_token' not found in user parameters.")
            sys.exit()