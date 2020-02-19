"""
Example script for resource allocation
"""
import os
import logging

from oet.domain import SubArray


LOG = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=logging.INFO, format=FORMAT)


def main(configuration, scan_duration, subarray_id=1, repeat=1, process_json=True):
    """
    Configure a sub-array and perform the scan.

    :param configuration: name of configuration file
    :param scan_duration: scan duration in seconds
    :param subarray_id: numeric subarray ID
    :param repeat: number of times to repeat the configure/scan
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

    for i in range(repeat):
        LOG.info(f'Scan {i+1} of {repeat}')

        LOG.info(f'Configure subarray from CDM: {configuration}')
        subarray.configure_from_file(configuration, with_processing=process_json)

        LOG.info(f'Perform scan for {scan_duration}s')
        subarray.scan(float(scan_duration))

    LOG.info('End scheduling block')
    subarray.end_sb()

    LOG.info('Observation script complete')
