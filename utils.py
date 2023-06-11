import pandas as pd
import json

# import pyyaml module
# install pip install pyyaml
import yaml
from yaml.loader import SafeLoader
from json import loads, dumps

def load_data_csv(data_path):
    return pd.read_csv(data_path, index_col=0)

def load_data_json(data_path):
    f = open (data_path, "r")
    # Reading from file
    data = json.loads(f.read())
    
    f.close()
    return data

def get_data_from_config_file(config_path = "./config.yaml"):
    with open(config_path) as f:
        data = yaml.load(f, Loader=SafeLoader)       
        return data
   
def load_data(data_path):
        return pd.read_csv(data_path, index_col=0) 

def write_result_to_pc (data, result_path):
    try:
        jsonString = json.dumps(data)
        text_file = open(result_path, "w")
        n = text_file.write(jsonString)
        text_file.close()
        return 1
    except:
        print("File to save does not exist !!!")
        return 0