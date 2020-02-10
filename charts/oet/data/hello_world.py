import logging
import os
import time

LOG = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=logging.INFO, format=FORMAT)

LOG.info(f'Importing module: {__name__}')


def main(*args, sleep=None, **kwargs):
    LOG.info(f'Running script in OS process {os.getpid()}')
    LOG.info(f'Received user args: {args}')
    LOG.info(f'Received user kwargs: {kwargs}')

    if sleep is not None:
        LOG.info(f'Now sleeping for {sleep} seconds')
        time.sleep(sleep)
        LOG.info('Sleep complete\n')
