import json 
import random
from random import choice
from datetime import date
from datetime import datetime
import csv
import re
import string
import logging
import os
from os.path import dirname, join
from ska_ser_skuid.client import SkuidClient
LOGGER = logging.getLogger(__name__)

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


def update_resource_config_file(file,disable_logging=False):
    with open(file, 'r') as f:
        data = json.load(f)
    if not disable_logging:
        LOGGER.info("READ file before update:" + str(data))
    client = SkuidClient(os.environ['SKUID_URL'])
    # New type of id "eb_id" is used to distinguish between real SB and id used during testing
    eb_id = client.fetch_skuid("eb")
    data["sdp"]["eb_id"] = eb_id
    if "processing_blocks" in data["sdp"]:
        for i in range(len(data["sdp"]["processing_blocks"])):
            pb_id = client.fetch_skuid("pb")
            data["sdp"]["processing_blocks"][i]["pb_id"] = pb_id
            if "dependencies" in data["sdp"]["processing_blocks"][i]:
                if i == 0:
                    data["sdp"]["processing_blocks"][i]["dependencies"][0]["pb_id"] = \
                        data["sdp"]["processing_blocks"][i]["pb_id"]
                else:
                    data["sdp"]["processing_blocks"][i]["dependencies"][0]["pb_id"] = \
                    data["sdp"]["processing_blocks"][i - 1]["pb_id"]
    LOGGER.info(data)
    with open(file, 'w') as f:
        json.dump(data, f)
    if not disable_logging:
        LOGGER.info("________ AssignResources Updated string for next iteration_______" + str(data))
        LOGGER.info("________ SDP block is_______" + str(data['sdp']))
    with open(file, 'r') as f:
        data1 = json.load(f)
    if not disable_logging:
        LOGGER.info("READ file after update:" + str(data1))
    return data['sdp']


def update_scan_config_file(file, sdp_block,disable_logging=False):
    with open(file, 'r') as f:
        data = json.load(f)
    if not disable_logging:
        LOGGER.info("________Configure string before update function _______" + str(file))
    sdp_sbi_id = sdp_block['eb_id']
    if not disable_logging:
        LOGGER.info("________Updated sdp_sbi_id from configure string _______" + str(sdp_sbi_id))
    data['csp']['common']['id'] = sdp_sbi_id + '-' + data['sdp']['scan_type']
    if not disable_logging:
        LOGGER.info("________Updated csp-id from configure string _______" + str(data['csp']['common']['id']))
    with open(file, 'w') as f:
        json.dump(data, f)
    if not disable_logging:
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
    with open(file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        data = []
        for row in reader:
            data.append(row)
    return data
