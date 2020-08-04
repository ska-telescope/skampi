import json 
import random
from random import choice
from datetime import date
from datetime import datetime
import csv
import re
import string
import logging

LOGGER = logging.getLogger(__name__)

def inc_from_old_nr(oldnr,incremental=1):
    #assumes trailing 5 digits is an integer counter unless succeeded with a dash and a non digit
    #also assumes we wont get increments hgher than 50 000 in a day
    # TODO : Commenting this logic to generate the number inc by 1
    LOGGER.info("Old nr:" + str(oldnr))
    # with 1 increment in id value
    # inc =  int(re.findall(r'\d{5}(?=$|-\D)',oldnr)[0])
    # LOGGER.info("Last 5 digits of ID:" + str(inc))  
    # old_inc = '{:05d}'.format(inc+incremental)
    # LOGGER.info("With inc by 1 logic updated increamented ID: " + str(old_inc))
    # Id generation with random numbers
    new_inc = f'{choice(range(0,99999)):05d}'
    # with timestamp value
    # (dt, micro) = datetime.utcnow().strftime('%S.%f').split('.')
    # new_inc = "%s%03d" % (dt, int(micro) / 1000)
    # LOGGER.info("With random generation logic updated ID:" + str(re.sub(r'\d{5}(?=$|-\D)',new_inc,oldnr)))
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
    LOGGER.info("READ file before update:" + str(data))
    data['sdp']['id'] = inc_from_old_nr(data['sdp']['id'])
    #assumes index nrs are following inbrokenly from loweest nr to highest nr in the list
    #this means each indix needs to inc by their range = size of the list
    incremental = len(data['sdp']['processing_blocks'])
    for index,item in enumerate(data['sdp']['processing_blocks']):
        if(index==0):
            data['sdp']['processing_blocks'][index]['id'] = inc_from_old_nr(item['id'],incremental)
            first_pb_id_num = data['sdp']['processing_blocks'][index]['id']
            next_pb_id_num =  int(re.findall(r'\d{5}(?=$|-\D)',first_pb_id_num)[0])
            LOGGER.info("Last 5 digits of ID:" + str(next_pb_id_num)) 
        else:
            next_pb_id_num += 1
            data['sdp']['processing_blocks'][index]['id'] =  re.sub(r'\d{5}(?=$|-\D)',str(next_pb_id_num).zfill(5),first_pb_id_num)
        if 'dependencies' in item.keys():
            for index2,item2 in enumerate(item['dependencies']):
                data['sdp']['processing_blocks'][index]['dependencies'][index2]['pb_id'] = data['sdp']['processing_blocks'][0]['id']
    with open(file, 'w') as f:
        json.dump(data, f)
        #f.write(json.dump(data))
    LOGGER.info("________ AssignResources Updated string for next iteration_______" + str(data))
    LOGGER.info("________ SDP block is_______" + str(data['sdp']))
    with open(file, 'r') as f:
        data1 = json.load(f)
    LOGGER.info("READ file after update:" + str(data1))
    return data['sdp']



def update_scan_config_file(file, sdp_block):
    with open(file, 'r') as f:
        data = json.load(f)
    LOGGER.info("________Configure string before update function _______" + str(file))
    sdp_sbi_id = sdp_block['id']
    LOGGER.info("________Updated sdp_sbi_id from configure string _______" + str(sdp_sbi_id))
    data['csp']['id'] = sdp_sbi_id + '-' + data['sdp']['scan_type']
    LOGGER.info("________Updated csp-id from configure string _______" + str(data['csp']['id']))
    with open(file, 'w') as f:
        json.dump(data, f)
    LOGGER.info("________ Configure Updated string for next iteration_______" + str(data))


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

def get_csv_file(file):
    with open('build/{}'.format(filename), 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        data = []
        for row in reader:
            data.append(row)
    return data
