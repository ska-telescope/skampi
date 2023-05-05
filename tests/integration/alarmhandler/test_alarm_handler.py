import pytest
import tango

"""Test to verify alarm-handler configuration"""

"""
Test Elettra Alarm Handler
"""


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
def test_load_alarm():
    """Test to load and verify the configured alarm."""
    alarm_device = tango.DeviceProxy("alarm/handler/01")
    alarm_device.command_inout(
        "Load",
        (
            "tag=test;formula=(sys/tg_test/1/attribute =="
            ' 0);priority=log;group=none;message=("alarm for current'
            ' attribute")'
        ),
    )
    tag = "test"
    searched_alarm = alarm_device.command_inout("SearchAlarm", tag)
    assert "test" in searched_alarm[0]
