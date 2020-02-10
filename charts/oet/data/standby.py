"""
Example script for telescope standby
"""
import logging
import os

from oet.domain import SKAMid

LOG = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=logging.INFO, format=FORMAT)


def main():
    """
    Telescope standby.
    """
    LOG.info(f'Running telescope standby script in OS process {os.getpid()}')

    LOG.info(f'Executing telescope standby...')
    telescope = SKAMid()
    telescope.standby()

    LOG.info('Telescope standby script complete')
