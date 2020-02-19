"""
Example script for telescope standby
"""
import logging
import os

from oet.domain import SKAMid

LOG = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=logging.INFO, format=FORMAT)


def main(*args, **kwargs):
    """
    Telescope standby.
    """
    LOG.info(f'Running telescope standby script in OS process {os.getpid()}')

    if args:
        LOG.warning('Got unexpected positional args: %s', args)
    if kwargs:
        LOG.warning('Got unexpected named args: %s', kwargs)

    LOG.info(f'Executing telescope standby...')
    telescope = SKAMid()
    telescope.standby()

    LOG.info('Telescope standby script complete')
