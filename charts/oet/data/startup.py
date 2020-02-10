"""
Example script for telescope startup
"""
import logging
import os

from oet.domain import SKAMid

LOG = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=logging.INFO, format=FORMAT)


def main():
    """
    Start up telescope.
    """
    LOG.info(f'Running telescope start-up script in OS process {os.getpid()}')

    telescope = SKAMid()

    LOG.info(f'Starting telescope...')
    telescope.start_up()

    LOG.info('Telescope start-up script complete')
