"""
Example script for resource allocation
"""
import logging
import os

from oet.domain import Dish, ResourceAllocation, SKAMid, SubArray

LOG = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=logging.INFO, format=FORMAT)


def main(subarray_id=1, dish_ids=None):
    """
    Allocate resources to a target sub-array.

    :param subarray_id: numeric subarray ID
    :param dish_ids: comma-separated dish IDs
    :return:
    """
    if dish_ids is None:
        dish_ids = []

    LOG.info(f'Running allocate script in OS process {os.getpid()}')
    LOG.info(f'Called with main(subarray_id={subarray_id}, dish_ids={dish_ids}')

    subarray = SubArray(subarray_id)

    dishes = [Dish(i) for i in dish_ids]
    allocation = ResourceAllocation(dishes=dishes)

    LOG.info(f'Allocating resources: {allocation}')
    allocated = subarray.allocate(allocation)
    LOG.info(f'Resources Allocated: {allocated}')

    LOG.info('Allocation script complete')
