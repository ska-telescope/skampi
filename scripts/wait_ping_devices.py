import tango

database = tango.Database()
instance_list = database.get_device_exported("*")
failed = 1000
while failed == 0:
    failed = 0
    for instance in instance_list.value_string:
        try:
            dev = tango.DeviceProxy(instance)
            dev.ping()
        except:
            failed = failed + 1
