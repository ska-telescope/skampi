"""
Example script for resource allocation
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


def _main(subarray_id: int, configuration, scan_duration, repeat=1, process_json=True):
    """
    Configure a sub-array and perform the scan.

    :param subarray_id: numeric subarray ID
    :param configuration: name of configuration file
    :param scan_duration: scan duration in seconds
    :param repeat: number of times to repeat the scan
    :param process_json: set to False to pass JSON directly to TMC without processing
    :return:
    """
    LOG.info(f'Running observe script in OS process {os.getpid()}')
    LOG.info(f'Called with main(configuration={configuration}, scan_duration={scan_duration}, '
             f'subarray_id={subarray_id})')

    if not os.path.isfile(configuration):
        msg = f'File not found: {configuration}'
        LOG.error(msg)
        raise IOError(msg)

    subarray = SubArray(subarray_id)

    LOG.info(f'Configure subarray from CDM: {configuration}'
             f'Scan duration: {scan_duration}')
    subarray.configure_from_file(configuration, scan_duration, 
                                 with_processing=process_json)

    for i in range(repeat):
        LOG.info(f'Scan {i+1} of {repeat}')
        LOG.info(f'Perform scan for {scan_duration}s')
        subarray.scan()

    LOG.info('End scheduling block')
    subarray.end()

    LOG.info('Observation script complete')
