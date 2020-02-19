#Imports
import sys, getopt
import json
from tango import DeviceProxy, DevFailed, AttributeProxy
from time import sleep
import os

def cm_configure_attributes():
    configure_success_count = 0
    configure_fail_count = 0
    already_configured_count = 0
    total_attrib_count = 0
    with open(attr_list_file, 'r') as attrib_list_file:
        attribute_list = json.load(attrib_list_file)
        for attribute in attribute_list:
            total_attrib_count += 1
            
            attribute_fqdn = "tango://" + os.environ['TANGO_HOST'] + "/" + attribute

            max_retries = 10
            sleep_time = 30
            for x in range(0, max_retries):
                try:
                    att = AttributeProxy(attribute_fqdn)
                    att.read()
                    break
                except DevFailed as df:
                    if(x == (max_retries -1)):
                        raise df
                    print("DevFailed exception: " + str(df.args[0].reason) + ". Sleeping for " + str(sleep_time) + "ss")
                    sleep(sleep_time)

            conf_manager_proxy.write_attribute("SetAttributeName", attribute_fqdn)
            conf_manager_proxy.write_attribute("SetArchiver", evt_subscriber_device_fqdn)
            conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")
            conf_manager_proxy.write_attribute("SetPollingPeriod", 1000)
            conf_manager_proxy.write_attribute("SetPeriodEvent", 3000)
            
            try:
                conf_manager_proxy.command_inout("AttributeAdd")
                configure_success_count += 1
                print ("attribute_fqdn " + attribute_fqdn + " " + " added successfuly")
            except DevFailed as df:
                if str(df.args[0].reason) == 'Already archived':
                    print("attribute_fqdn " + attribute_fqdn + " " + str(df.args[0].reason))
                    already_configured_count += 1
                    configure_success_count += 1
                    continue
                print("Exception: ", str(df))
                configure_fail_count += 1
                continue
    return configure_success_count, configure_fail_count, already_configured_count, total_attrib_count

def start_archiving(str_attribute):
    conf_manager_proxy.command_inout("AttributeStart", str_attribute)

def remove_attribute(str_attribute):
    conf_manager_proxy.command_inout("AttributeRemove", str_attribute)

# Main entrypoint of the script.
conf_manager_device_fqdn = ""
evt_subscriber_device_fqdn = ""
attr_list_file = ""
## parse arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "c:e:a:", ["cm=", "es=", "attrfile="])
except getopt.GetoptError:
    print("Please provide proper arguments.")
    print("Usage: $python configure_hdbpp.py --cm=<FQDN> --es=<FQDN> --attrfile=<filepath> OR")
    print("       $python configure_hdbpp.py -cm <FQDN> -e <FQDN> -a <filepath>")
    print("       cm: FQDN of HDB++ Configuration Manager")
    print("       es: FQDN of HDB++ Event subscriber")
    print("       infile: File containing FQDNs of attributes to archive")
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-c", "--cm"):
        conf_manager_device_fqdn = arg
    elif opt in ("-e", "--es"):
        evt_subscriber_device_fqdn = arg
    elif  opt in ("-a", "--attrfile"):
        attr_list_file = arg

conf_manager_proxy = DeviceProxy(conf_manager_device_fqdn)
evt_subscriber_proxy = DeviceProxy(evt_subscriber_device_fqdn)

conf_manager_proxy.set_timeout_millis(5000)
evt_subscriber_proxy.set_timeout_millis(5000)

configure_success_count, configure_fail_count, already_configured_count, total_attrib_count = cm_configure_attributes()

print("Configured successfully: ", configure_success_count, "Failed: ", configure_fail_count, "Already configured: ", already_configured_count, "Total attributes: ", total_attrib_count)
if configure_fail_count > 0:
    exit(-1)

evt_subscriber_proxy.Start()
