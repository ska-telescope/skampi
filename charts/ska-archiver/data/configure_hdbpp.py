"Script to configure hdbpp archiver"
# Imports
import sys
import getopt
import json
from time import sleep
import os
from tango import DeviceProxy, DevFailed, AttributeProxy


def cm_configure_attributes():
    """Method to configure an attribute."""
    configure_success_count = 0
    configure_fail_count = 0
    already_configured_count = 0
    total_attrib_count = 0
    attribute_started_count = 0
    error_starting_attrib_count = 0
    with open(ATTR_LIST_FILE, 'r') as attrib_list_file:
        configuration_blocks = json.load(attrib_list_file)
        for c_b in configuration_blocks:
            attribute_list = c_b['attributes']
            polling_period = c_b['polling_period']
            period_event = c_b['period_event']

            attr_started_list = evt_subscriber_proxy.read_attribute("AttributeStartedList").value
            if attr_started_list is not None:
                for started_attr in attr_started_list:
                    if started_attr in attribute_list:
                        attribute_list.remove(started_attr)

            for attribute in attribute_list:
                total_attrib_count += 1

                # attribute_fqdn = "tango://" + str(tango_host) + "/" + attribute
                attribute_fqdn = attribute

                is_already_archived = False
                attr_list = evt_subscriber_proxy.read_attribute("AttributeList").value
                sleep(10)
                if attr_list is not None:
                    for already_archived in attr_list:
                        if attribute.lower() in str(already_archived).lower():
                            print("Attribute " + attribute + " already configured.")
                            is_already_archived = True
                            already_configured_count += 1
                            attribute_started_count, error_starting_attrib_count = \
                                start_archiving(attribute, attribute_started_count,
                                                error_starting_attrib_count)
                            break

                if not is_already_archived:
                    print("Attribute " + attribute + " not configured. Configuring it now. ")
                    max_retries = 5
                    sleep_time = 1
                    not_online = False
                    for loop_cnt in range(0, max_retries):
                        try:
                            att = AttributeProxy(attribute_fqdn)
                            att.read()
                            break
                        except DevFailed as dev_failed:
                            if loop_cnt == (max_retries - 1):
                                print("Attribute " + attribute + " not online. Skipping it.")
                                not_online = True
                                break
                            print("DevFailed exception: " + str(dev_failed.args[0].reason) +
                                  ". Sleeping for " + str(sleep_time) + "ss")
                            sleep(sleep_time)

                    if not_online:
                        continue

                    try:
                        conf_manager_proxy.write_attribute("SetAttributeName", attribute_fqdn)
                        conf_manager_proxy.write_attribute("SetArchiver",
                                                           EVT_SUBSCRIBER_DEVICE_FQDN)
                        conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")
                        conf_manager_proxy.write_attribute("SetPollingPeriod", int(polling_period))
                        conf_manager_proxy.write_attribute("SetPeriodEvent", int(period_event))
                    except Exception as except_occured:
                        print("Exception while setting configuration manager arrtibutes: ",
                              except_occured)
                        configure_fail_count += 1
                        continue

                    try:
                        conf_manager_proxy.AttributeAdd()
                        sleep(5)
                        configure_success_count += 1
                        print("attribute_fqdn " + attribute_fqdn + " " + " added successfuly")

                    except DevFailed as dev_failed:
                        configure_fail_count += 1
                        print("Exception occured while adding attribute for archiving: ",
                              dev_failed)


    return configure_success_count, configure_fail_count, already_configured_count, \
            total_attrib_count, attribute_started_count, error_starting_attrib_count


def start_archiving(str_attribute, attribute_started, error_starting_attrib):
    """Method to start archiving an attribute."""
    try:
        conf_manager_proxy.command_inout("AttributeStart", str_attribute)
        attribute_started += 1
        print("Archiving for " + str_attribute + " has been started successfully.")
    except Exception as except_occured:
        error_starting_attrib += 1
        print("start_archiving except_occured: ", except_occured)

    return attribute_started, error_starting_attrib


# Main entrypoint of the script.
CONF_MANAGER_DEVICE_FQDN = ""
EVT_SUBSCRIBER_DEVICE_FQDN = ""
ATTR_LIST_FILE = ""
tango_host = ""
# parse arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "c:e:a:h:", ["cm=", "es=", "attrfile=", "th="])

except getopt.GetoptError:
    print("Please provide proper arguments.")
    print("Usage: $python configure_hdbpp.py --cm=<FQDN> --es=<FQDN> --attrfile=<filepath> --th=<TANGO_HOST> OR")
    print("       $python configure_hdbpp.py -cm <FQDN> -e <FQDN> -a <filepath> -h <TANGO_HOST>")
    print("       cm: FQDN of HDB++ Configuration Manager")
    print("       es: FQDN of HDB++ Event subscriber")
    print("       infile: File containing FQDNs of attributes to archive")
    print("       th: TANGO_HOST of the device on which MVP is running")
    sys.exit(2)
for opt, arg in opts:
    if opt in ("-c", "--cm"):
        CONF_MANAGER_DEVICE_FQDN = arg
    elif opt in ("-e", "--es"):
        EVT_SUBSCRIBER_DEVICE_FQDN = arg
    elif opt in ("-a", "--attrfile"):
        ATTR_LIST_FILE = arg
    elif opt in ("-h", "--th"):
        tango_host = arg

conf_manager_proxy = DeviceProxy(CONF_MANAGER_DEVICE_FQDN)
evt_subscriber_proxy = DeviceProxy(EVT_SUBSCRIBER_DEVICE_FQDN)

SLEEP_TIME = 6
MAX_RETRIES = 10
for x in range(0, MAX_RETRIES):
    try:
        configure_success_attr_count, configure_fail_attr_count, already_configured_attr_count, \
         total_attribute_count, attr_started_archiving_count, error_starting_attr_count = \
         cm_configure_attributes()
        print("\nConfigured successfully:", configure_success_attr_count, ", Failed:",
              configure_fail_attr_count, ", Already configured:",
              already_configured_attr_count, ", Total attributes: ",
              total_attribute_count, ", Attribute started:", attr_started_archiving_count,
              ", Error starting attribute:", error_starting_attr_count)
        break
    except Exception:
        print("configure_attribute exception: " + str(sys.exc_info()))
        if x == (MAX_RETRIES - 1):
            sys.exit(-1)

    try:
        DEVICE_ADM = None
        DEVICE_ADM = DeviceProxy("dserver/hdbppcm-srv/01")
        DEVICE_ADM.RestartServer()
    except Exception:
        print("reset_conf_manager exception: " + str(sys.exc_info()[0]))

    sleep(SLEEP_TIME)

if configure_fail_attr_count > 0:
    sys.exit(-1)

evt_subscriber_proxy.Start()
