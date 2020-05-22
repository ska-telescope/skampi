"""
Example script for resource allocation
"""

from time import sleep
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy

ALLOC_FAIL_MSG = "Script failed to allocate resources"
DEALLOC_FAIL_MSG = "Script failed to deallocate resources"

def pause():
    sleep(4)

def test_allocation(telescope, subarray, allocation):
    "test that resources can be allocated and deallocated from a given subarray"

    print("Starting up telescope ...")
    telescope.start_up()

    print("Releasing any previously allocated resources... ")
    result = subarray.deallocate()
    pause()

    print("Allocating new resources... ")
    result = subarray.allocate(allocation)
    pause()

    assert (
        result == allocation) \
            , ALLOC_FAIL_MSG + " result was : " + str(result)

    # Confirm result via direct inspection of TMC
    subarray_proxy = DeviceProxy('ska_mid/tm_subarray_node/1')
    pause()
    receptor_list = subarray_proxy.receptorIDList
    pause()
    assert (
        str(receptor_list) == "(1, 2)") \
            , ALLOC_FAIL_MSG + " result was : " + str(receptor_list)

    print("Resources Allocated :" + str(result))

    print("Now deallocating resources ... ")
    subarray.deallocate()
    pause()

    # Confirm result via direct inspection of TMC - expecting None 
    receptor_list = subarray_proxy.receptorIDList
    pause()
    assert (
        receptor_list is None), DEALLOC_FAIL_MSG + " result was : " + receptor_list

    print("Subarry has no allocated resources")

    # put telescope to standby
    telescope.standby()
    print("Script Complete: All resources dealoccated, Telescope is in standby")


if __name__ == "__main__":

    TELESCOPE = SKAMid()
    SUBARRAY = SubArray(1)
    RESOURCES = ResourceAllocation(dishes=[Dish(1), Dish(2)])

    test_allocation(TELESCOPE, SUBARRAY, RESOURCES)
