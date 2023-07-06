import pandas as pd
import json

# import pyyaml module
# pip install pyyaml
# pip install bs4
# pip install unicode

import yaml
from yaml.loader import SafeLoader
from json import loads, dumps
from bs4 import BeautifulSoup

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

def config_exist_or_init(config_path = "./config.yaml", template_path= "./config_template.yaml"):
    open(config_path, 'a+').close()
    with open(config_path, 'r+') as f:
        data = yaml.load(f, Loader=SafeLoader)
        
        if(data and len(data.keys()) > 0):
            return True
        else:
            if(not data):
                data = {}
            with open(template_path) as f2:
                data2 = yaml.load(f2, Loader=SafeLoader)
                for key in data2.keys():
                    data[key] = ''
                
                yaml.dump(data, f)

def set_value_in_config(key, value, config_path= "./config.yaml"):
    with open(config_path, 'r+') as f:
        doc = yaml.load(f, Loader=SafeLoader)
        doc[key] = value
        yaml.dump(doc, f)
   
def load_data(data_path):
        return pd.read_csv(data_path, index_col=0) 

def write_result_to_pc (data, result_path):
    try:
        jsonString = json.dumps(data, indent=4, sort_keys=True)
        text_file = open(result_path, "w")
        n = text_file.write(jsonString)
        text_file.close()
        return 1
    except:
        print("File to save does not exist !!!")
        return 0

def write_html (data, html_path):
    output_html = add_to_html(data, html_path)
    try:
        
        text_file = open(html_path, "w")
        text_file.write(output_html)
        text_file.close()
        return 1
    except:
        print("Html file to save does not exist !!!")
        return 0

def create_html_file (html_path):
    try:
        text_file = open(html_path, "w")
        text_file.write('')
        text_file.close()
        return 1
    except:
        print("Html file to save does not exist !!!")
        return 0
    
def add_to_html (data, html_path):
    try:
        f = open (html_path, "r")
        # Reading from file
        read_data = f.read()
        
        output_doc = BeautifulSoup()
        output_doc.append(output_doc.new_tag("html"))
        output_doc.html.append(output_doc.new_tag("head"))
        output_doc.head.extend(BeautifulSoup('<title> Results from query </title>', "html.parser"))
        
        output_doc.html.append(output_doc.new_tag("body"))
        
        if(data):
            output_doc.body.extend(BeautifulSoup(data, "html.parser").body)
        if(read_data):
            output_doc.body.extend(BeautifulSoup(read_data, "html.parser").body)
        
        f.close()
        
        ret_html = '<!DOCTYPE html>' + output_doc.prettify()
        
        return ret_html
    except:
        print("Html file to save does not exist !!!")
        return 0