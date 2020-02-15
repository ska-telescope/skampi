import pytest
import sys
sys.path.append('/app')

import mock
from tests.acceptance_tests.helpers import *
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from assertpy import assert_that

class TestResource(object):
    def test_init(self):
        """
        Test the __init__ method.
        """
        name = 'name'
        r = resource(name)
        assert r.device_name == name

    def mock_start_up():
        pass

    @mock.patch('oet.domain.SKAMid')
    @mock.patch('oet.domain.SubArray')
    def test_assign_resources(self,subarray_mock,telescope_mock):
        allocation = ResourceAllocation(dishes= [Dish(1), Dish(2), Dish(3), Dish(4)])
        telescope_mock.start_up= self.mock_start_up
        subarray_mock.allocate.return_value = allocation
        result = take_subarray(1).to_be_composed_out_of(4)
        telescope_mock.start_up.assert_called_once()
        subarray_mock.allocate.asser_called_once()
        assert_that(result).is_equal_to(ResourceAllocation(dishes= [Dish(1), Dish(2), Dish(3), Dish(4)]))
