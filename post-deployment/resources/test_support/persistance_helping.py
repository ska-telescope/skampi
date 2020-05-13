import json 
import random
from random import choice
from datetime import date
import csv
import re


def inc_from_old_nr(oldnr,incremental=1):
    #assumes trailing 5 digits is an integer counter unless succeeded with a dash and a non digit
    #also assumes we wont get increments hgher than 50 000 in a day
    inc =  int(re.findall(r'\d{5}(?=$|-\D)',oldnr)[0])  
    new_inc = '{:05d}'.format(inc+incremental)
    return re.sub(r'\d{5}(?=$|-\D)',new_inc,oldnr)

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

def update_resource_config_file(file):
    with open(file, 'r') as f:
        data = json.load(f)
    data['sdp']['id'] = inc_from_old_nr(data['sdp']['id'])
    #assumes index nrs are following inbrokenly from loweest nr to highest nr in the list
    #this means each indix needs to inc by their range = size of the list
    incremental = len(data['sdp']['processing_blocks'])
    for index,item in enumerate(data['sdp']['processing_blocks']):
        data['sdp']['processing_blocks'][index]['id'] = inc_from_old_nr(item['id'],incremental)
        if 'dependencies' in item.keys():
            for index2,item2 in enumerate(item['dependencies']):
                data['sdp']['processing_blocks'][index]['dependencies'][index2]['pb_id'] = inc_from_old_nr(item2['pb_id'],incremental)
    with open(file, 'w') as f:
        json.dump(data, f)

def update_scan_config_file(file):
    with open(file, 'r') as f:
        data = json.load(f)
    data['csp']['id'] = inc_from_old_nr(data['csp']['id'])
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