"""
Example script for abort sub-array activity
"""
import functools
import logging
import os

from oet.domain import SubArray

LOG = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=logging.INFO, format=FORMAT)


def main(*args, **kwargs):
    LOG.warning('Deprecated! Calling main before sub-array is bound will be removed for PI9')
    _main(*args, **kwargs)


def init(subarray_id: int):
    global main
    main = functools.partial(_main, subarray_id)
    LOG.info(f'Script bound to sub-array {subarray_id}')


def _main(subarray_id: int, *args, **kwargs):
    """
    Send the 'abort' command to the SubArrayNode, halt the subarray
    activity.

    :param subarray_id: numeric subarray ID
    :return:
    """
    LOG.info(f'Running abort script in OS process {os.getpid()}')

    if args:
        LOG.warning('Got unexpected positional args: %s', args)
    if kwargs:
        LOG.warning('Got unexpected named args: %s', kwargs)

    LOG.info(f'Called with main(subarray_id={subarray_id})')

    subarray = SubArray(subarray_id)

    LOG.info(f'aborting subarray {subarray_id} activity')

    subarray.abort()

    LOG.info('Observation script complete')

