"""
Example script for resetting sub-array. Resetting will keep allocated dishes.
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
    Reset SubArray. SubArray state should be IDLE if reset is successful.

    :param subarray_id: numeric subarray ID
    """
    LOG.info(f'Running SubArray reset script in OS process {os.getpid()}')

    if args:
        LOG.warning('Got unexpected positional args: %s', args)
    if kwargs:
        LOG.warning('Got unexpected named args: %s', kwargs)

    LOG.info(f'Executing reset...')
    subarray = SubArray(subarray_id)
    subarray.reset()

    LOG.info('SubArray reset script complete')
