import getopt, sys
import tango
from tango import Database
from tango import ConnectionFailed, CommunicationFailed, DevFailed

HOSTNAME = ""
DBNAME = ""

try:
    opts, args = getopt.getopt(sys.argv[1:], "h:d", ["hostname=", "dbname="])

except getopt.GetoptError:
    print("Please provide proper arguments.")
    print("Usage: $python lib_configuration.py --hostname=<hostname> --dbname=<dbname> ")
    print("       $python configure_hdbpp.py -h <hostname> -d <dbname>")
    print("       hn: Host name of the machine on which database is running")
    print("       dn: Database name")
    sys.exit(2)

for opt, arg in opts:
    if opt in ("-h", "--hostname"):
        HOSTNAME = arg
    elif opt in ("-d", "--dbname"):
        DBNAME = arg

try:
    print("Configuring hostname and dbname for CM and ES...")
    DB_NAME = Database()
    hostname = HOSTNAME 
    libname = "libhdb++mysql.so.6"
    dbname = DBNAME
    port = 3306
    user = "tango"
    password = "tango"

    host_name = "host={}".format(hostname)
    lib_name = "libname={}".format(libname)
    db_name = "dbname={}".format(dbname)
    port_number = "port={}".format(port)
    user_name = "user={}".format(user)
    user_password = "password={}".format(password)
    
    prop = {"LibConfiguration": [host_name, lib_name, db_name, port_number, user_name, user_password]}

    DB_NAME.put_device_property("archiving/hdbpp/eventsubscriber01", prop)
    DB_NAME.put_device_property("archiving/hdbpp/confmanager01", prop)
    print("Updated LibConfiguration property:")
    print("FOR ES: ", DB_NAME.get_device_property("archiving/hdbpp/eventsubscriber01", "LibConfiguration"))
    print("FOR CM: ", DB_NAME.get_device_property("archiving/hdbpp/confmanager01", "LibConfiguration"))

except (ConnectionFailed, CommunicationFailed, DevFailed) as exception:
    print("Exception occured: ", exception)