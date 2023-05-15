import tango
import time

TIMEOUT=60
database = tango.Database()
failed = 1000
start_time = time.time()
print("TANGO waiting start")
while failed > 0:
    elapsed_time = time.time() - start_time
    if elapsed_time > TIMEOUT:
        print("Devices not working: exiting tango wait with failure")
        exit(1)
    failed = 0
    instance_list = database.get_device_exported("*")
    for instance in instance_list.value_string:
        try:
            dev = tango.DeviceProxy(instance)
            dev.ping()
            print("Got ping working for dev %s" + str(instance))
        except:
            failed = failed + 1
            print("Got exception for dev %s" + str(instance))
elapsed_time = time.time() - start_time
print("TANGO waiting: all devices working in %s ss.", int(elapsed_time))
