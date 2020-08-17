"""
Example script for SB-driven observation resource allocation from file
"""
import functools
import logging
import os

from ska.cdm.messages.central_node.assign_resources import AssignResourcesRequest
from ska.cdm.messages.central_node.assign_resources import DishAllocation as cdm_DishAllocation
from ska.cdm.messages.central_node.assign_resources import \
    ProcessingBlockConfiguration as cdm_ProcessingBlockConfiguration, \
    PbDependency as cdm_PbDependency, SDPWorkflow as cdm_SDPWorkflow
from ska.cdm.messages.central_node.assign_resources import SDPConfiguration as cdm_SDPConfiguration
from ska.cdm.messages.central_node.assign_resources import ScanType as cdm_ScanType, Channel as cdm_Channel
from ska.cdm.schemas import CODEC as cdm_CODEC
from ska.pdm.entities.dish_allocation import DishAllocation as pdm_DishAllocation
from ska.pdm.entities.sb_definition import SBDefinition
from ska.pdm.entities.sdp.processing_block import ProcessingBlock as pdm_ProcessingBlock, \
    PbDependency as pdm_PbDependency, Workflow as pdm_Workflow
from ska.pdm.entities.sdp.scan_type import ScanType as pdm_ScanType, Channel as pdm_Channel
from ska.pdm.entities.sdp.sdp_configuration import SDPConfiguration as pdm_SDPConfiguration
from ska.pdm.schemas import CODEC as pdm_CODEC
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


def _main(subarray_id: int, sb_json, allocate_json='', update_uids=True):
    """
    Allocate resources to a target sub-array using a Scheduling Block (SB).

    :param subarray_id: numeric subarray ID
    :param sb_json: file containing SB in JSON format
    :param allocate_json: name of configuration file
    :param update_uids: True if UIDs should be updated
    :return:
    """
    LOG.info(f'Running allocate script in OS process {os.getpid()}')
    LOG.info(
        f'Called with main(sb_json={sb_json}, configuration={allocate_json}, subarray_id={subarray_id}, update_uids={update_uids}')

    if not os.path.isfile(sb_json):
        msg = f'SB file not found: {sb_json}'
        LOG.error(msg)
        raise IOError(msg)

    if not allocate_json:
        cdm_allocation_request = AssignResourcesRequest(subarray_id, None, None)
    elif not os.path.isfile(allocate_json) :
        msg = f'CDM file not found: {allocate_json}'
        LOG.error(msg)
        raise IOError(msg)
    else:
        cdm_allocation_request: AssignResourcesRequest = cdm_CODEC.load_from_file(AssignResourcesRequest, allocate_json)

    pdm_allocation_request: SBDefinition = pdm_CODEC.load_from_file(SBDefinition, sb_json)

    # Configure PDM DishAllocation to the equivalent CDM DishAllocation
    pdm_dish = pdm_allocation_request.dish_allocations
    cdm_dish = convert_dishallocation(pdm_dish)
    LOG.info(f'Setting dish : {cdm_dish.receptor_ids} ')

    # Configure PDM SDPConfiguration to the equivalent CDM SDPConfiguration
    pdm_sdp_config = pdm_allocation_request.sdp_configuration
    cdm_sdp_config = convert_sdpconfiguration(pdm_sdp_config, pdm_allocation_request.field_configurations)
    LOG.info(f'Setting SDP configuration : {cdm_sdp_config.sdp_id} ')

    cdm_allocation_request.dish = cdm_dish
    cdm_allocation_request.sdp_config = cdm_sdp_config

    # In order to rerun the same SBI multiple times, we must update the IDs
    # otherwise SDP complains about duplicate SBI ids being resourced.
    # The following workaround is a temporary measure. In production a new SBI
    # with new self-consistent UIDs would be created by another application so
    # no UIDS would be modified in the script itself.

    if update_uids:
        update_all_uids(cdm_allocation_request.sdp_config)

    response = observingtasks.assign_resources_from_cdm(subarray_id, cdm_allocation_request)
    LOG.info(f'Resources Allocated: {response}')

    LOG.info('Allocation script complete')


def update_all_uids(sdp_config: cdm_SDPConfiguration):
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


def convert_dishallocation(pdm_config: pdm_DishAllocation) -> cdm_DishAllocation:
    """
    Convert a PDM DishAllocation to the equivalent CDM DishAllocation.
    """

    return cdm_DishAllocation(
        receptor_ids=pdm_config.receptor_ids
    )


def convert_sdpconfiguration(pdm_config: pdm_SDPConfiguration, pdm_field_configuration) -> cdm_SDPConfiguration:
    """
    Convert a PDM SDPConfiguration to the equivalent CDM SDPConfiguration.
    """
    scan_types = [convert_scantypes(obj, pdm_field_configuration) for obj in pdm_config.scan_types]
    processing_blocks = [convert_processing_blocks(obj) for obj in pdm_config.processing_blocks]

    return cdm_SDPConfiguration(
        sdp_id=pdm_config.sdp_id,
        max_length=pdm_config.max_length,
        scan_types=scan_types,
        processing_blocks=processing_blocks

    )


def convert_processing_blocks(pdm_config: pdm_ProcessingBlock) -> cdm_ProcessingBlockConfiguration:
    """
    Convert a PDM ProcessingBlock to the equivalent CDM ProcessingBlockConfiguration.
    """
    if pdm_config.dependencies:
        pdm_dependencies = [convert_dependencies(obj) for obj in pdm_config.dependencies]
    else:
        pdm_dependencies = None
    pdm_workflow = convert_workflow(pdm_config.workflow)
    LOG.info(f'Setting ProcessingBlock Id : {pdm_config.pb_id} ')
    return cdm_ProcessingBlockConfiguration(
        pb_id=pdm_config.pb_id,
        workflow=pdm_workflow,
        parameters=pdm_config.parameters,
        dependencies=pdm_dependencies
    )


def convert_workflow(pdm_config: pdm_Workflow) -> cdm_SDPWorkflow:
    """
    Convert a PDM Workflow to the equivalent CDM SDPWorkflow.
    """
    LOG.info(f'Setting Workflow Id : {pdm_config.workflow_id} ')
    return cdm_SDPWorkflow(
        workflow_id=pdm_config.workflow_id,
        workflow_type=pdm_config.workflow_type,
        version=pdm_config.version
    )


def convert_dependencies(pdm_config: pdm_PbDependency) -> cdm_PbDependency:
    """
    Convert a PDM PbDependency to the equivalent CDM PbDependency.
    """
    LOG.info(f'Setting PbDependency Id : {pdm_config.pb_id} ')
    return cdm_PbDependency(
        pb_id=pdm_config.pb_id,
        pb_type=pdm_config.pb_type
    )


def convert_scantypes(pdm_config: pdm_ScanType, pdm_field_configuration) -> cdm_ScanType:
    """
    Convert a PDM ScanType to the equivalent CDM ScanType.
    """

    channels = [convert_channels(obj) for obj in pdm_config.channels]
    system, ra, dec = get_targets(pdm_config.target_id, pdm_field_configuration)
    LOG.info(f'Setting scanType Id : {pdm_config.st_id} ')
    return cdm_ScanType(
        st_id=pdm_config.st_id,
        coordinate_system=system,
        ra=ra,
        dec=dec,
        channels=channels,

    )


def get_targets(target_id, pdm_field_configuration):
    """
     Get target attributes ra, dec, system from PDM field configuration
     based on target_id reference in scanType
    """
    for pdm_field_configuration_id in pdm_field_configuration:
        if pdm_field_configuration_id.targets[0].id == target_id:
            frame_name = pdm_field_configuration_id.targets[0].coord.frame.name
            icrs_coord = pdm_field_configuration_id.targets[0].coord.transform_to(frame_name)
            hms, dms = icrs_coord.to_string('hmsdms', sep=':').split(' ')
            ra = hms
            dec = dms
            system = icrs_coord.frame.name
            LOG.info(f'Setting Target attribute for targetid:{target_id} -> system:{system} , ra:{ra} ,'
                     f' dec:{dec}')
            return system, ra, dec


def convert_channels(pdm_config: pdm_Channel) -> cdm_Channel:
    """
     Convert a PDM Channel to the equivalent CDM Channel.
    """
    LOG.info(f'Setting channel attribute -> count:{pdm_config.count} , start:{pdm_config.start} ,'
             f' stride:{pdm_config.stride}, freq_min:{pdm_config.freq_min}, freq_max:{pdm_config.freq_max} ,'
             f' link_map:{pdm_config.link_map} ')
    return cdm_Channel(
        count=pdm_config.count,
        start=pdm_config.start,
        stride=pdm_config.stride,
        freq_min=pdm_config.freq_min,
        freq_max=pdm_config.freq_max,
        link_map=pdm_config.link_map
    )

