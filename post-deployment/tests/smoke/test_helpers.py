"""
Tests for helpers.py
"""
import sys
sys.path.append('/app')

import importlib
import mock
from mock import Mock
import tango
from assertpy import assert_that
from resources.test_support.helpers import resource, take_subarray, waiter, subscriber, watch
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from resources.test_support.helpers import *
import pytest

class TestResource():
    @pytest.mark.fast
    def test_init(self):
        """
        Test the __init__ method.
        """
        device_name = 'name'
        item_under_test = resource(device_name)
        assert item_under_test.device_name == device_name

    @mock.patch('resources.test_support.helpers.DeviceProxy')
    @pytest.mark.fast
    def get_attribute_info_ex(self, name, data_type):
        """
        Return AttributeInfoEx object.
        """
        attr_info_ex = tango.AttributeInfoEx()
        attr_info_ex.data_type = data_type
        attr_info_ex.name = name
        return attr_info_ex

    @mock.patch('resources.test_support.helpers.DeviceProxy')
    @pytest.mark.fast
    def test_get_attr_enum(self, mock_proxy):
        """
        Test the get method.
        Enum attribute name is returned.
        DeviceProxy used by resource is mocked.
        """
        # Create AttributeInfoEx object for enum attribute
        attr_info_ex = tango.AttributeInfoEx()
        attr_info_ex.data_type = tango._tango.CmdArgType.DevEnum
        attr_info_ex.name = 'enumAttribute'
        # Set for mock attribute and return values of methods
        attribute_list = 'buildState,versionId,enumAttribute'
        mock_proxy.return_value.get_attribute_list.return_value = attribute_list
        mock_proxy.return_value._get_attribute_config.return_value = attr_info_ex
        mock_proxy.return_value.enumAttribute = attr_info_ex
        # Create instance of resource to test
        device_name = 'device'
        item_under_test = resource(device_name)
        assert item_under_test.get('enumAttribute') == attr_info_ex.name

    @mock.patch('resources.test_support.helpers.DeviceProxy')
    @pytest.mark.fast
    def test_get_attr_not_found(self, mock_proxy):
        """
        Test the get method.
        Attribute name is not in the attribute list.
        DeviceProxy used by resource is mocked.
        """
        #importlib.reload(sys.modules[resource.__module__])
        # Set for mock return value of method
        attribute_list = 'buildState,versionId,enumAttribute'
        mock_proxy.return_value.get_attribute_list.return_value = attribute_list
        # Create instance of resource to test
        device_name = 'device'
        item_under_test = resource(device_name)
        assert item_under_test.get('nonexistent attribute') == 'attribute not found'

@mock.patch('resources.test_support.helpers.SubArray.allocate')
@mock.patch('resources.test_support.helpers.waiter')
@pytest.mark.fast
def test_pilot_compose_subarray(waiter_mock, subarray_mock_allocate):
    allocation = ResourceAllocation(dishes=[Dish(1), Dish(2), Dish(3), Dish(4)])
    take_subarray(1).to_be_composed_out_of(4)
    dish_devices = [
        'mid_d0001/elt/master', 'mid_d0002/elt/master',
        'mid_d0003/elt/master', 'mid_d0004/elt/master',
        ]
    waiter_mock_instance = waiter_mock.return_value
    waiter_mock_instance.set_wait_for_assign_resources.assert_called_once()
    waiter_mock_instance.wait.assert_called_once()
    subarray_mock_allocate.assert_called_once_with(allocation)

@mock.patch('resources.test_support.helpers.watch')
@mock.patch('resources.test_support.helpers.resource')
@mock.patch('resources.test_support.helpers.subscriber')
@pytest.mark.fast
def test_tearing_down_subarray(subscriber_mock, resource_mock, watch_mock):
    the_waiter = waiter()
    the_waiter.set_wait_for_tearing_down_subarray()
    assert_that(resource_mock.call_count).is_equal_to(5)
    #assert_that(subscriber_mock.call_count).is_equal_to(5+4)
    #assert_that(watch_mock.call_count).is_equal_to(5+4)
    the_waiter.wait()

@pytest.mark.fast
def test_wait_for_change():
    resource_mock = Mock(spec=resource)
    resource_mock.device_name = "test_device"
    resource_mock.get.return_value = "value_then"
    watch = monitor(resource_mock, "value_then", "attr")
    result = watch.wait_until_value_changed(10)
    assert_that(result).is_equal_to("timeout")
    resource_mock.get.return_value = "value_now"
    result = watch.wait_until_value_changed(10)
    assert_that(result).is_equal_to(9)

@pytest.mark.fast
def test_state_changer():
    resource_mock = Mock(spec=resource)
    resource_mock.device_name = "test_device" 
    resource_mock.get.return_value = "value_then"
    result = wait_for(resource_mock,10).to_be({"attr":"mock_attr","value":"value_then"})
    assert_that(result).is_equal_to(10)
    result = wait_for(resource_mock,1).to_be({"attr":"mock_attr","value":"value_now"})
    assert_that(result).is_equal_to("timed out")
