from resources.test_support.controls import restart_subarray
from assertpy import assert_that
import mock
import pytest
import logging


fake_device_mapping = {'device_1':1,'device_2':2,'device_3':1}
@pytest.mark.fast
@mock.patch('resources.test_support.controls.resource')
@mock.patch('resources.test_support.controls.waiter')
@mock.patch('resources.test_support.controls.device_to_subarrays',new=fake_device_mapping)
def test_restart_subarray(mock_waiter,mock_resource):
    #given
    mock_resource_instance = mock_resource.return_value
    #when
    restart_subarray(1)
    assert_that(mock_resource_instance.restart.call_count).is_equal_to(2)

@pytest.mark.fast
@mock.patch('resources.test_support.controls.resource')
@mock.patch('resources.test_support.controls.device_to_subarrays',new=fake_device_mapping)
def test_handle_exceptions_on_sub_array_restart(mock_resource):
    #given
    mock_resource_instance = mock_resource.return_value
    mock_resource_instance.restart.side_effect = Exception('Exception_123')
    #when
    with pytest.raises(Exception, match=r".*\nException raised on reseting device_1:Exception_123\nException raised on reseting device_3:Exception_123.*"):
        restart_subarray(1)

