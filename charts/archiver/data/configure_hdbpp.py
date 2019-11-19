
#Imports
import sys, getopt
import json
from tango import DeviceProxy, DevFailed
from time import sleep

def cm_configure_attributes():
    configure_success_count = 0
    configure_fail_count = 0
    already_configured_count = 0
    total_attrib_count = 0

    with open(attr_list_file, 'r') as attrib_list_file:
        attribute_list = json.load(attrib_list_file)
        for attribute in attribute_list:
            total_attrib_count += 1
            ## Set appropriate CM attributes
            try:
                # SetAttributeName
                conf_manager_proxy.write_attribute("SetAttributeName", attribute)

                # SetArchiver
                conf_manager_proxy.write_attribute("SetArchiver", evt_subscriber_device_fqdn)

                # SetStrategy
                conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")

                # SetPollingPeriod
                conf_manager_proxy.write_attribute("SetPollingPeriod", 1000)

                # SetEventPeriod
                conf_manager_proxy.write_attribute("SetPeriodEvent", 3000)
            except Exception as except_occured:
                print("Exception while setting configuration manage arrtibutes: ", except_occured)
                configure_fail_count += 1
                continue

            ## Add Attribute for archiving
            try:
                conf_manager_proxy.command_inout("AttributeAdd")
            except DevFailed as df:
                str_df = str(df)
                if "reason = Already archived" in str_df:
                    start_archiving(attribute)
                else:
                    already_configured_count += 1
                    continue

            configure_success_count += 1

    return configure_success_count, configure_fail_count, already_configured_count, total_attrib_count

def start_archiving(str_attribute):
    try:
        conf_manager_proxy.command_inout("AttributeStart", str_attribute)
    except Exception as except_occured:
        print("start_archiving except_occured: ", except_occured)

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



timeSleep = 30
for x in range(10):
    try:
        print ("create device proxies")
         # create device proxies
        conf_manager_proxy = DeviceProxy(conf_manager_device_fqdn)
        evt_subscriber_proxy = DeviceProxy(evt_subscriber_device_fqdn)
        break
    except:
        print ("Could not connect to device proxies. Retry after " + str(timeSleep) + " seconds.")
        sleep(timeSleep)

try:
    # configure attribute
    configure_success_count, configure_fail_count, already_configured_count, total_attrib_count = cm_configure_attributes()
    print("Configured successfully: ", configure_success_count, "Failed: ", configure_fail_count,
          "Already configured: ", already_configured_count, "Total attributes: ", total_attrib_count
          )
except Exception as exception:
    print("Exception: ", exception)