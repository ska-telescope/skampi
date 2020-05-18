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
#SUT
from resources.test_support.helpers import resource, take_subarray, waiter, subscriber, watch,monitor,wait_for
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
#SUT framework (not part of test)
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish

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
        Return Atfrom resources.log_consumer.tracer_helper import TraceHelpertributeInfoEx object.
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
    waiter_mock_instance = waiter_mock.return_value
    waiter_mock_instance.timed_out = False
    take_subarray(1).to_be_composed_out_of(4)
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
    with pytest.raises(Exception):
        assert watch.wait_until_value_changed(10)

class mock_resource():

    def __init__(self,nr_of_retries=5):
        self.get_counter = 0
        self.nr_of_retries = nr_of_retries
        self.device_name = 'dummy resources'

    def get(self,value):
        self.get_counter +=1
        if value == 'no_change':
            return value
        if self.get_counter == self.nr_of_retries:
            return "future_value"
        else:
            return value



@pytest.mark.fast
def test_transition():
    wait = watch(mock_resource(nr_of_retries=5)).for_a_change_on('mock_att',changed_to='mock_att')   
    result = wait.wait_until_value_changed(timeout=9)
    assert_that(result).is_equal_to(4)


@pytest.mark.fast
def test_wait_for_change_and_to_future_value():
    wait = watch(mock_resource(nr_of_retries=5)).for_a_change_on('mock_att',changed_to='future_value')
    result = wait.wait_until_value_changed(timeout=9)
    assert_that(result).is_equal_to(5)

@pytest.mark.fast
def test_wait_for_change_and_to_future_value_timeout_on_future():
    wait = watch(mock_resource(nr_of_retries=5)).for_a_change_on('mock_att',changed_to='missing_value')
    with pytest.raises(Exception):
        wait.wait_until_value_changed(timeout=9)

@pytest.mark.fast  
def test_wait_for_change_timeout():
    wait = watch(mock_resource(nr_of_retries=5)).for_a_change_on('no_change')
    with pytest.raises(Exception):
        wait.wait_until_value_changed(timeout=9)

@pytest.mark.fast
def test_state_changer():
    resource_mock = Mock(spec=resource)
    resource_mock.device_name = "test_device" 
    resource_mock.get.return_value = "value_then"
    result = wait_for(resource_mock,10).to_be({"attr":"mock_attr","value":"value_then"})
    assert_that(result).is_equal_to(10)
    result = wait_for(resource_mock,1).to_be({"attr":"mock_attr","value":"value_now"})
    assert_that(result).is_equal_to("timed out")
