import getopt, sys
import tango
from tango import Database
from tango import ConnectionFailed, CommunicationFailed, DevFailed
from tango import DeviceProxy, DevFailed, AttributeProxy
import time

HOSTNAME = ""
DBNAME = ""
CONF_MANAGER_DEVICE_FQDN = ""
EVT_SUBSCRIBER_DEVICE_FQDN = ""
tango_host = ""

try:
    opts, args = getopt.getopt(sys.argv[1:], "c:e:h:d", ["cm=", "es=", "hostname=", "dbname="])

except getopt.GetoptError:
    print("Please provide proper arguments.")
    print("Usage: $python lib_configuration.py --cm=<FQDN> --es=<FQDN> --hostname=<hostname> --dbname=<dbname> ")
    print("       $python configure_hdbpp.py -cm <FQDN> -e <FQDN> -h <hostname> -d <dbname>")
    print("       cm: FQDN of HDB++ Configuration Manager")
    print("       es: FQDN of HDB++ Event subscriber")
    print("       hn: Host name of the machine on which database is running")
    print("       dn: Database name")
    sys.exit(2)

for opt, arg in opts:
    if opt in ("-c", "--cm"):
        CONF_MANAGER_DEVICE_FQDN = arg
    elif opt in ("-e", "--es"):
        EVT_SUBSCRIBER_DEVICE_FQDN = arg
    if opt in ("-h", "--hostname"):
        HOSTNAME = arg
    elif opt in ("-d", "--dbname"):
        DBNAME = arg

try:
    conf_manager_proxy = DeviceProxy(CONF_MANAGER_DEVICE_FQDN)
    evt_subscriber_proxy = DeviceProxy(EVT_SUBSCRIBER_DEVICE_FQDN)
    
    DB_NAME = Database()
    hostname = HOSTNAME 
    libname = "libhdb++mysql.so.6"
    dbname = DBNAME
    port = 3306
    user = "eda_admin"
    password = "@v3ng3rs@ss3mbl3"

    host_name = "host={}".format(hostname)
    lib_name = "libname={}".format(libname)
    db_name = "dbname={}".format(dbname)
    port_number = "port={}".format(port)
    user_name = "user={}".format(user)
    user_password = "password={}".format(password)
    
    prop = {"LibConfiguration": [host_name, lib_name, db_name, port_number, user_name, user_password]}

    DB_NAME.put_device_property("archiving/hdbpp/eventsubscriber01", prop)
    DB_NAME.put_device_property("archiving/hdbpp/confmanager01", prop)
    print("Updated hostname and dbname for CM and ES...")

except (ConnectionFailed, CommunicationFailed, DevFailed) as exception:
    print("Exception occured: ", exception)

# conf_manager_admin = conf_manager_proxy.adm_name()
# evt_subscriber_admin = evt_subscriber_proxy.adm_name()

# print("conf_manager_admin", conf_manager_admin)
# print("evt_subscriber_admin", evt_subscriber_admin)
cm_admin_proxy = DeviceProxy("dserver/hdbppcm-srv/01")
es_admin_proxy = DeviceProxy("dserver/hdbppes-srv/01")

# print("Restarting ES and CM..")
cm_admin_proxy.RestartServer()
# time.sleep(4)
#print("State CM: ", str(conf_manager_proxy.State()))
es_admin_proxy.RestartServer()
time.sleep(5)
# print("State CM: ", str(conf_manager_proxy.State()))
# print("State ES: ", str(evt_subscriber_proxy.State()))

# while True:
#     print("In While loop")
#     try:
#         if((str(conf_manager_proxy.State()) == "ON") and (str(evt_subscriber_proxy.State()) == "ON")):
#             print("State CM: ", str(conf_manager_proxy.State()))
#             print("State ES: ", str(evt_subscriber_proxy.State()))
#             break
#         else:
#             print("In else")
#             time.sleep(2)
#     except Exception as exc:
#         print("Exception: ", str(exc))
#         time.sleep(2)
#         continue
