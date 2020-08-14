"""
Example script for resource allocation from file
"""
import functools
import logging
import os

from ska.cdm.messages.central_node.assign_resources import AssignResourcesRequest
from ska.cdm.messages.central_node.assign_resources import SDPConfiguration
from ska.cdm.schemas import CODEC as cdm_CODEC
from skuid.client import SkuidClient

from oet import observingtasks

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


def _main(subarray_id, allocate_json, update_uids=True):
    """
    Allocate resources to a target sub-array.

    :param subarray_id: numeric subarray ID
    :param allocate_json: name of configuration file
    :param update_uids: True if UIDs should be updated
    :return:
    """
    LOG.info(f'Running allocate script in OS process {os.getpid()}')
    LOG.info(f'Called with main(configuration={allocate_json}, subarray_id={subarray_id}, update_uids={update_uids}')

    request: AssignResourcesRequest = cdm_CODEC.load_from_file(AssignResourcesRequest, allocate_json)

    # In order to rerun the same SBI multiple times, we must update the IDs
    # otherwise SDP complains about duplicate SBI ids being resourced.
    # The following workaround is a temporary measure. In production a new SBI
    # with new self-consistent UIDs would be created by another application so
    # no UIDS would be modified in the script itself.
    if update_uids:
        update_all_uids(request.sdp_config)

    response = observingtasks.assign_resources_from_cdm(subarray_id, request)
    LOG.info(f'Resources Allocated: {response}')

    LOG.info('Allocation script complete')


def update_all_uids(sdp_config: SDPConfiguration):
    """
    Replace UIDs with fresh UIDs retrieved from the UID generator.

    This function modifies the SDPConfiguration in-place.

    :param sdp_config: SDP configuration to process
    :return:
    """
    LOG.info(f'Updating UIDs')
    uid_client = SkuidClient(os.environ['SKUID_URL'])

    # Create a mapping of old SB IDs to new IDs
    new_sbi_mapping = {sdp_config.sdp_id: uid_client.fetch_skuid('sbi')}
    for old_id, new_id in new_sbi_mapping.items():
        LOG.info(f'New SBI ID mapping: {old_id} -> {new_id}')

    # Create a mapping of old processing block IDs to new IDs
    new_pb_mapping = {pb.pb_id: uid_client.fetch_skuid('pb')
                      for pb in sdp_config.processing_blocks}
    for old_id, new_id in new_pb_mapping.items():
        LOG.info(f'New PB ID mapping: {old_id} -> {new_id}')

    # Trawl through the SDP configuration replacing old IDs with new
    sdp_config.sdp_id = new_sbi_mapping[sdp_config.sdp_id]
    for pb in sdp_config.processing_blocks:
        pb.pb_id = new_pb_mapping[pb.pb_id]
        if pb.dependencies:
            for dependency in pb.dependencies:
                dependency.pb_id = new_pb_mapping[dependency.pb_id]
