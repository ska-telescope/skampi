"""
Tests for helpers.py
"""
import sys
sys.path.append('/app')

import importlib
import mock
from mock import Mock,MagicMock
import logging
import tango
from tango import TimeVal
from assertpy import assert_that
#SUT
from resources.test_support.helpers import resource, waiter, subscriber, watch,monitor,wait_for,AttributeWatcher
from resources.test_support.controls import take_subarray
#SUT framework (not part of test)
from ska.scripting.domain import SKAMid, SubArray, ResourceAllocation, Dish

import pytest

class TestResource():
    @pytest.mark.fast
    @pytest.mark.skamid
    def test_init(self):
        """
        Test the __init__ method.
        """
        device_name = 'name'
        item_under_test = resource(device_name)
        assert item_under_test.device_name == device_name

    @mock.patch('resources.test_support.helpers.DeviceProxy')
    @pytest.mark.fast
    @pytest.mark.skamid
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
    @pytest.mark.skamid
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
    @pytest.mark.skamid
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

class fake_resource():

    def __init__(self,getvalue):
        self.get_value = getvalue

    def get(self,attr):
        return self.get_value

    def assert_attribute(self,attribute):
        return fake_comparison()

class fake_comparison():

    def equals(self,value):
        return None;

#mock_resource = Mock(unsafe=True)
@mock.patch('resources.test_support.sync_decorators.resource')
@mock.patch('resources.test_support.controls.SubArray.allocate_from_file')
@mock.patch('resources.test_support.sync_decorators.waiter')
@pytest.mark.fast
@pytest.mark.skamid
def test_pilot_compose_subarray(waiter_mock, subarray_mock_allocate,mock_resource):
    allocation = ResourceAllocation(dishes=[Dish(1), Dish(2), Dish(3), Dish(4)])
    mock_resource.return_value = Mock(unsafe=True)
    waiter_mock_instance = waiter_mock.return_value
    waiter_mock_instance.timed_out = False
    take_subarray(1).to_be_composed_out_of(4)
    waiter_mock_instance.set_wait_for_assign_resources.assert_called_once()
    waiter_mock_instance.wait.assert_called_once()
    subarray_mock_allocate.assert_called_once_with('resources/test_data/OET_integration/example_allocate.json',allocation)

@mock.patch('resources.test_support.helpers.watch')
@mock.patch('resources.test_support.helpers.resource')
@mock.patch('resources.test_support.helpers.subscriber')
@pytest.mark.fast
@pytest.mark.skamid
def test_tearing_down_subarray(subscriber_mock, resource_mock, watch_mock):
    the_waiter = waiter()
    mon_mock_instance = watch_mock.return_value.for_any_change_on.return_value
    mon_mock_instance2 = watch_mock.return_value.to_become.return_value
    mon_mock_instance.wait_until_conditions_met.return_value = 10
    mon_mock_instance2.wait_until_conditions_met.return_value = 10
    the_waiter.set_wait_for_tearing_down_subarray()
    assert_that(resource_mock.call_count).is_equal_to(3)
    #assert_that(subscriber_mock.call_count).is_equal_to(5+4)
    #assert_that(watch_mock.call_count).is_equal_to(5+4)
    the_waiter.wait()


@pytest.mark.fast
@pytest.mark.skamid
def test_wait_for_change_exception():
    resource_mock = Mock(spec=resource)
    resource_mock.device_name = "test_device"
    resource_mock.get.return_value = "value_then"
    watch = monitor(resource_mock, "value_then", "attr",require_transition=True)
    with pytest.raises(Exception):
        assert watch.wait_until_value_changed(10)
    


@pytest.mark.fast
@pytest.mark.skamid
def test_wait_for_change_success():
    resource_mock = Mock(spec=resource)
    resource_mock.device_name = "test_device"
    values = ['1','1','2','2']
    #use pop to emulate value events being pushed. the order is from left to right if we give  a param of 0
    resource_mock.get = values.pop
    watch = monitor(resource_mock, "1", 0,require_transition=True)
    result = watch.wait_until_value_changed(5)
    assert_that(result).is_equal_to(2)

@pytest.mark.fast
@pytest.mark.skamid
def test_wait_for_desired_value_no_change():
    resource_mock = Mock(spec=resource)
    resource_mock.device_name = "test_device"
    values = ['1','1','2','2']
    resource_mock.get = values.pop
    watch = monitor(resource_mock, "1", 0,future_value="1",require_transition=False)
    result = watch.wait_until_value_changed(5)
    assert_that(result).is_equal_to(5)




# mock get attribute from a resource
#the get method will provide three possible returns:
#1. the value is the same as the name of the attribute -> this is what it starts at
#2, the value is the same as the future value_> changed after nr of retries is exceeded
#3, the value changes to a future value that is different to the expected one
change_to_future =[
    'old value',
    'old value',
    'old value',
    'new value',
    'too far'
]
change_to_none = [
        'old value',
        'old value',
        'old value',
        'old value',
        'too far'
]
transition_seq = [
        'start',
        'start',
        'transition',
        'transition',
        'start',
        'too far']

transition_tuple = [
        (0,0,0,0),
        (0,0,0,0),
        (0,0,0,0),
        (1,1,0,0),
        (1,1,0,0),
        (1,1,0,0)]

class MockResource():
    
    def __init__(self,seq):
        self.seq  = seq
        self.index=-1
        self.device_name = 'mock device'

    def get(self,attr):
        self.index +=1
        return self.seq[self.index]




@pytest.mark.fast
def test_transition():
    #test that the a change in value from one to another and then back to original stil gets picked up
    mock_resource = MockResource(transition_seq)
    wait = watch(mock_resource).for_a_change_on('mock_att',changed_to='start')   
    result = wait.wait_until_value_changed(timeout=9)
    assert_that(result).is_equal_to(5)

def test_transition_with_predicate():
    future_value = (1,1,0,0)
    mock_resource = MockResource(transition_tuple)
    def predicate_inst(current,expected):
        return (sum(current) == sum(expected))
    wait = watch(mock_resource).for_a_change_on('mock_att',changed_to=future_value,predicate=predicate_inst) 
    result = wait.wait_until_value_changed(timeout=9)
    assert_that(result).is_equal_to(6)

@pytest.mark.fast
def test_wait_for_change_and_to_future_value():
    mock_resource = MockResource(change_to_future)
    wait = watch(mock_resource).for_a_change_on('mock_att',changed_to='new value')
    result = wait.wait_until_value_changed(timeout=9)
    assert_that(result).is_equal_to(6)

@pytest.mark.fast
def test_wait_for_change_and_to_future_value_timeout_on_future():
    mock_resource = MockResource(change_to_future)
    wait = watch(mock_resource).for_a_change_on('mock_att',changed_to='missing_value')
    with pytest.raises(Exception):
        wait.wait_until_value_changed(timeout=5)

@pytest.mark.fast  
def test_wait_for_change_timeout():
    mock_resource = MockResource(change_to_none)
    wait = watch(mock_resource).for_a_change_on('no_change')
    with pytest.raises(Exception):
        wait.wait_until_value_changed(timeout=3)

@pytest.mark.fast
def test_state_changer():
    resource_mock = Mock(spec=resource)
    resource_mock.device_name = "test_device" 
    resource_mock.get.return_value = "value_then"
    result = wait_for(resource_mock,10).to_be({"attr":"mock_attr","value":"value_then"})
    assert_that(result).is_equal_to(10)
    result = wait_for(resource_mock,1).to_be({"attr":"mock_attr","value":"value_now"})
    assert_that(result).is_equal_to("timed out")

@mock.patch('resources.test_support.helpers.signal')
@mock.patch('resources.test_support.helpers.DeviceProxy')
@mock.patch('resources.test_support.helpers.threading.Event')
def test_subscribe_with_attribute_watcher(mock_signal,devicemock,mock_event):
    #when I create a watch
    w = AttributeWatcher(resource('fake_device'),'fake_attribute','fake_desired')
    #I expect a subscription to have occurred
    devicemock.return_value.subscribe_event.assert_called_once()
    #given then that the device calls the callback
    event_mock = Mock(spec = tango.EventData)
    event_mock.attr_value.return_value = 'current value'
    w._cb(event_mock)
    w.result_available.set.assert_not_called()
    #then when I wait
    w._wait(5)
    w.result_available.wait.assert_called_once()
    #then if a new event is passed 
    event_mock.attr_value.return_value = 'fake_desired'
    w._cb(event_mock)
    


def load_events(events):
    mock_events = []
    for index,event in enumerate(events):
        mock_event = Mock(spec = tango.EventData)
        mock_event.attr_value.value = event
        mock_event.reception_date = TimeVal(index)
        mock_events.append(mock_event)
    return mock_events

@mock.patch('resources.test_support.helpers.signal')
@mock.patch('resources.test_support.helpers.DeviceProxy')
@mock.patch('resources.test_support.helpers.threading.Event') 
def test_wait_for_desired_attribute_watcher(stub_signal,devicestub,stub_event):
    #given
    w = watch(resource('fake_dev'),implementation='tango_events').to_become('fake_att',changed_to='ready')
    events = [
        'wait',
        'wait',
        'wait',
        'ready',
        'ready'
    ]
    mock_events = load_events(events)
    #when
    for mock_event in mock_events[:3]:
        w._cb(mock_event)
    #then
    w.result_available.set.assert_not_called()
    #when
    w._cb(mock_events[3])
    w.result_available.set.assert_called_once()

@mock.patch('resources.test_support.helpers.signal')
@mock.patch('resources.test_support.helpers.DeviceProxy')
@mock.patch('resources.test_support.helpers.threading.Event') 
def test_wait_for_change_attribute_watcher(stub_signal,devicestub,stub_event):
    #given
    w = watch(resource('fake_dev'),implementation='tango_events').for_any_change_on('fake_att')
    events = [
        'wait',
        'wait',
        'wait',
        'wait',
        'ready'
    ]
    mock_events = load_events(events)
    #when
    for mock_event in mock_events[:4]:
        w._cb(mock_event)
    #then
    w.result_available.set.assert_not_called()
    #when
    w._cb(mock_events[4])
    w.result_available.set.assert_called_once()

@mock.patch('resources.test_support.helpers.signal')
@mock.patch('resources.test_support.helpers.DeviceProxy')
@mock.patch('resources.test_support.helpers.threading.Event') 
def test_wait_for_transition_attribute_watcher(stub_signal,devicestub,stub_event):
    #given
    w = watch(resource('fake_dev'),implementation='tango_events').for_a_change_on('fake_att',changed_to='wait')
    events = [
        'wait',
        'ready',
        'ready',
        'ready',
        'wait'
    ]
    mock_events = load_events(events)
    #when
    for mock_event in mock_events[:4]:
        w._cb(mock_event)
    #then
    w.result_available.set.assert_not_called()
    #when
    w._cb(mock_events[4])
    w.result_available.set.assert_called_once()


@mock.patch('resources.test_support.helpers.signal')
@mock.patch('resources.test_support.helpers.DeviceProxy')
@mock.patch('resources.test_support.helpers.threading.Event') 
def test_get_waiting_time_attribute_watcher(stub_signal,devicestub,stub_event):
       #given
    w = watch(resource('fake_dev'),implementation='tango_events').for_a_change_on('fake_att',changed_to='wait')
    events = [
        'wait',
        'ready',
        'ready',
        'ready',
        'wait'
    ]
    mock_events = load_events(events)
    #when
    for mock_event in mock_events[:5]:
        w._cb(mock_event)
    
    elapsed_time = w.wait_until_conditions_met(5)
    assert_that(elapsed_time).is_equal_to(4)

