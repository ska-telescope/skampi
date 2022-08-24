from tango import DeviceProxy

db = DeviceProxy("sys/database/2")
db.command_inout("DbGetDeviceInfo", "sys/tg_test/1")


def test_i_can_get_tango_db():
    testdevice = DeviceProxy("sys/tg_test/1")
    testdevice.ping()

    db = DeviceProxy("sys/database/2")
    db.ping()
    db.command_inout("DbGetDeviceInfo", "sys/tg_test/1")
