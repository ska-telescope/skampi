import sys
sys.path.append('/app')

import importlib
import mock
import tango
from assertpy import assert_that
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from test_support.helpers import *

class TestResource():
    def test_init(self):
        """
        Test the __init__ method.
        """
        device_name = 'name'
        item_under_test = resource(device_name)
        assert item_under_test.device_name == device_name

    @mock.patch('tango.DeviceProxy')
    def test_get_attr_enum(self, mock_proxy):
        """
        Test the get method.
        Enum attribute name is returned.
        DeviceProxy used by resource is mocked.
        """
        importlib.reload(sys.modules[resource.__module__])
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

    @mock.patch('tango.DeviceProxy')
    def test_get_attr_not_found(self, mock_proxy):
        """
        Test the get method.
        Attribute name is not in the attribute list.
        DeviceProxy used by resource is mocked.
        """
        importlib.reload(sys.modules[resource.__module__])
        # Set for mock return value of method
        attribute_list = 'buildState,versionId,enumAttribute'
        mock_proxy.return_value.get_attribute_list.return_value = attribute_list
        # Create instance of resource to test
        device_name = 'device'
        item_under_test = resource(device_name)

        assert item_under_test.get('nonexistent attribute') == 'attribute not found'

    def mock_start_up():
        pass

@mock.patch('test_support.helpers.SubArray.allocate')
@mock.patch('test_support.helpers.waiter')
def test_pilot_compose_subarray(waiter_mock,subarray_mock_allocate):
    allocation = ResourceAllocation(dishes= [Dish(1), Dish(2), Dish(3), Dish(4)])
    take_subarray(1).to_be_composed_out_of(4)
    dish_devices = ['mid_d0001/elt/master','mid_d0002/elt/master','mid_d0003/elt/master','mid_d0004/elt/master']
    waiter_mock_instance = waiter_mock.return_value
    waiter_mock_instance.set_wait_for_assign_resources.assert_called_once()
    waiter_mock_instance.wait.assert_called_once()
    subarray_mock_allocate.assert_called_once_with(allocation)
