import pytest
from tango import DeviceProxy,EventType
from assertpy import assert_that

def test_dish_subscribe():

    def callback(event):
        pass
    # assert I can subscribe 
    proxy = DeviceProxy('mid_d0001/elt/master')
    sub_id = proxy.subscribe_event('State', EventType.CHANGE_EVENT, callback )
    proxy.unsubscribe_event(sub_id)