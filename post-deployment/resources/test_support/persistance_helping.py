import json 
import random
from random import choice
from datetime import date
import csv

def update_file(file):
    import os 
    try:
        os.chdir('post-deployment')
    except: # ignores if this is an error (assumes then that we are already on that directory)
        pass
    with open(file, 'r') as f:
        data = json.load(f)
    random_no = random.randint(100, 999)
    data['scanID'] = random_no
    data['sdp']['configure'][0]['id'] = "realtime-" + date.today().strftime("%Y%m%d") + "-" + str(choice
                                                                                                  (range(1, 10000)))
    fieldid = 1
    intervalms = 1400

    scan_details = {}
    scan_details["fieldId"] = fieldid
    scan_details["intervalMs"] = intervalms
    scanParameters = {}
    scanParameters[random_no] = scan_details

    data['sdp']['configure'][0]['scanParameters'] = scanParameters

    with open(file, 'w') as f:
        json.dump(data, f)

def print_dict_to_file(filename,data):
    with open(filename, 'w') as file:
        file.write(json.dumps(data)) 

def print_dict_to_csv_file(filename,data):
    csv_columns = data[0].keys()
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def load_config_from_file(filename):
    with open(filename, 'r') as file:
        return file.read()