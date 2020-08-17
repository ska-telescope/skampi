"""
Example script for an SB-driven observation.
"""
import functools
import logging
import os
from datetime import timedelta

from astropy.coordinates import SkyCoord
from ska.cdm.messages.subarray_node.configure import ConfigureRequest
from ska.cdm.messages.subarray_node.configure import DishConfiguration as cdm_DishConfiguration
from ska.cdm.messages.subarray_node.configure import PointingConfiguration as cdm_PointingConfiguration
from ska.cdm.messages.subarray_node.configure import Target as cdm_Target
from ska.cdm.messages.subarray_node.configure.core import ReceiverBand as cdm_ReceiverBand
from ska.cdm.messages.subarray_node.configure.csp import CSPConfiguration as cdm_CSPConfiguration
from ska.cdm.messages.subarray_node.configure.csp import FSPConfiguration as cdm_FSPConfiguration
from ska.cdm.messages.subarray_node.configure.csp import FSPFunctionMode as cdm_FSPFunctionMode
from ska.cdm.messages.subarray_node.configure.tmc import TMCConfiguration as cdm_TMCConfiguration
from ska.cdm.messages.subarray_node.configure.sdp import SDPConfiguration as cdm_SDPConfiguration
from ska.cdm.schemas import CODEC as cdm_CODEC
from ska.pdm.entities.csp_configuration import CSPConfiguration as pdm_CSPConfiguration
from ska.pdm.entities.csp_configuration import FSPConfiguration as pdm_FSPConfiguration
from ska.pdm.entities.dish_configuration import DishConfiguration
from ska.pdm.entities.field_configuration import FieldConfiguration
from ska.pdm.entities.sb_definition import SBDefinition
from ska.pdm.entities.scan_definition import ScanDefinition
from ska.pdm.schemas import CODEC as pdm_CODEC

from oet import observingtasks
from oet.command import SCAN_ID_GENERATOR
from oet.domain import SubArray

LOG = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'

logging.basicConfig(level=logging.INFO, format=FORMAT)

#
# Changelog
#
# v1 number of scans and scan duration are sourced from SB
# v2 pointing information is sourced from SB
# v3 dish receiver comes from SB
# v4 csp is sourced from the SB
#


def main(*args, **kwargs):
    LOG.warning('Deprecated! Calling main before sub-array is bound will be removed for PI9')
    _main(*args, **kwargs)


def init(subarray_id: int):
    global main
    main = functools.partial(_main, subarray_id)
    LOG.info(f'Script bound to sub-array {subarray_id}')


def _main(subarray_id: int, sb_json, configure_json=None):
    """
    Observe using a Scheduling Block (SB) and template CDM file.

    :param subarray_id: numeric subarray ID
    :param sb_json: file containing SB in JSON format
    :param configure_json: configuration file in JSON format
    :return:
    """
    LOG.info(f'Running observe_sb script in OS process {os.getpid()}')
    LOG.info(f'Called with sb_json={sb_json}, configure_json={configure_json}, '
             f'subarray_id={subarray_id})')

    if not os.path.isfile(sb_json):
        msg = f'SB file not found: {sb_json}'
        LOG.error(msg)
        raise IOError(msg)

    # Potentially call these within a try ... except block
    sched_block: SBDefinition = pdm_CODEC.load_from_file(SBDefinition, sb_json)
    if configure_json:
        if not os.path.isfile(configure_json):
            msg = f'CDM file not found: {configure_json}'
            LOG.error(msg)
            raise IOError(msg)

        cdm_config: ConfigureRequest = cdm_CODEC.load_from_file(ConfigureRequest, configure_json)
    else:
        cdm_config: ConfigureRequest = ConfigureRequest()

    subarray = SubArray(subarray_id)

    LOG.info(f'Starting observing for scheduling block: {sched_block.id}')

    # Scan sequence is an ordered list of ScanDefinition identifiers. These
    # are string IDs, not the ScanDefinition instances themselves.
    # We need the ScanDefinition with matching ID. We could inspect each
    # ScanDefinition and return the one with matching ID, or we could do
    # as we do here, creating a look-up table and retrieving by key.
    # The advantage of this is that we can create the table outside of
    # the loop, therefore creating it once rather than once per iteration.
    scan_definitions = {scan_definition.id: scan_definition
                        for scan_definition in sched_block.scan_definitions}

    # Similarly we will need a look-up table for the FieldConfigurations as
    # the scan definitions contain only the FieldConfiguration IDs..
    field_configurations = {field_configuration.id: field_configuration
                            for field_configuration in sched_block.field_configurations}

    # ... same for dish configurations..
    dish_configurations = {dish_configuration.id: dish_configuration
                           for dish_configuration in sched_block.dish_configurations}

    # ... and for CSP configurations too.
    csp_configurations = {csp_configuration.csp_id: csp_configuration
                          for csp_configuration in sched_block.csp_configurations}

    for scan_definition_id in sched_block.scan_sequence:
        # Get the scan ID. This is only used for logging, not for any
        # business logic.
        scan_id = SCAN_ID_GENERATOR.value

        scan_definition = scan_definitions[scan_definition_id]
        LOG.info(f'Configuring for scan definition: {scan_definition.id}')

        # The Science Field Configuration is referenced by ID in the
        # scan definition
        field_configuration_id = scan_definition.field_configuration_id
        field_configuration = field_configurations[field_configuration_id]

        # Override the scan duration specified in the CDM with the scan
        # duration extracted from the SB. Note that the CDM library requires
        # scan durations to be timedelta instances, not floats.
        cdm_config.tmc = to_tmcconfiguration(scan_definition)
        # LOG.info(f'Set CDM TMC configuration: {cdm_config.tmc}')

        # Now override the pointing with that found in the SB target
        cdm_config.pointing = to_pointingconfiguration(field_configuration)
        # LOG.info(f'Set CDM pointing configuration: {cdm_config.pointing}')

        # The dish configuration is referenced by ID in the scan definition.
        # Get the dish configuration ID from the scan definition.
        if scan_definition.dish_configuration_id in dish_configurations:
            dish_configuration = dish_configurations[scan_definition.dish_configuration_id]
            cdm_config.dish = to_dishconfiguration(dish_configuration)
            # LOG.info(f'Set CDM dish configuration: {cdm_config.dish}')
        else:
            LOG.info(f'Known dish configurations: {dish_configurations}')
            raise KeyError(f'Dish configuration not found: {scan_definition.dish_configuration_id}')

        # Set CDM CSP configuration for scan.
        # This test checks both that the CSP ID is defined for the scan, and
        # that the CSP configuration was defined in the SB
        if scan_definition.csp_configuration_id in csp_configurations:
            pdm_cspconfiguration = csp_configurations[scan_definition.csp_configuration_id]
            cdm_config.csp = to_cspconfiguration(pdm_cspconfiguration)

            # Complete the CSP configuration by setting the frequency band from
            # the dish configuration for this scan.
            cdm_config.csp.frequency_band = cdm_config.dish.receiver_band

            # LOG.info(f'Set CSP configuration: {cdm_config.csp}')
        else:
            LOG.info(f'Known configurations: {csp_configurations}')
            raise KeyError(f'CSP configuration not found: {scan_definition.csp_configuration_id}')

        cdm_config.sdp = to_sdpconfiguration(scan_definition)

        # With the CDM modified, we can now issue the Configure instruction...
        LOG.info(f'Configuring subarray {subarray_id} for scan {scan_id}')
        observingtasks.configure_from_cdm(subarray_id, cdm_config)

        # .. and with configuration complete, we can begin the scan.
        LOG.info(f'Starting scan {scan_id}')
        subarray.scan()

    # All scans are complete. Observations are concluded with an 'end'
    # command.
    LOG.info(f'End scheduling block: {sched_block.id}')
    subarray.end()

    LOG.info('Observation script complete')


def to_cspconfiguration(pdm_config: pdm_CSPConfiguration) -> cdm_CSPConfiguration:
    """
    Convert a PDM CSPConfiguration to the equivalent CDM CSPConfiguration.
    """
    fsp_configs = [to_fspconfiguration(o) for o in pdm_config.fsp_configs]

    return pdm_CSPConfiguration(
        csp_id=pdm_config.csp_id,
        fsp_configs=fsp_configs
    )


def to_fspconfiguration(pdm_config: pdm_FSPConfiguration) -> cdm_FSPConfiguration:
    """
    Convert a PDM FSPConfiguration to the equivalent CDM FSPConfiguration.
    """
    return cdm_FSPConfiguration(
        fsp_id=pdm_config.fsp_id,
        function_mode=cdm_FSPFunctionMode(pdm_config.function_mode.value),
        frequency_slice_id=pdm_config.frequency_slice_id,
        integration_time=pdm_config.integration_time,
        corr_bandwidth=pdm_config.corr_bandwidth,
        channel_averaging_map=pdm_config.channel_averaging_map,
        output_link_map=pdm_config.output_link_map,
        fsp_channel_offset=pdm_config.fsp_channel_offset,
        zoom_window_tuning=pdm_config.zoom_window_tuning
    )


def to_tmcconfiguration(scan_definition: ScanDefinition) -> cdm_TMCConfiguration:
    """
    Convert a PDM ScanDefinition to the equivalent TMC configuration
    """
    LOG.info(f'Setting TMC configuration: {scan_definition.scan_duration}')
    return cdm_TMCConfiguration(
        scan_duration=timedelta(seconds=scan_definition.scan_duration)
    )


def to_pointingconfiguration(field_configuration: FieldConfiguration) -> cdm_PointingConfiguration:
    """
    Convert a PDM ScanDefinition to the equivalent TMC configuration
    """
    # Now override the pointing with that found in the SB target
    pdm_targets = field_configuration.targets
    # assume just using the first target for SKA MID. SKA LOW, with its
    # multiple beams, might be different.
    pdm_target = pdm_targets[0]

    coord: SkyCoord = pdm_target.coord
    raw_ra = coord.ra.value
    raw_dec = coord.dec.value
    units = (coord.ra.unit.name, coord.dec.unit.name)
    frame = coord.frame.name
    name = pdm_target.name

    LOG.info(f'Setting CDM pointing: {pdm_target}')
    return cdm_PointingConfiguration(
        target=cdm_Target(
            ra=raw_ra,
            dec=raw_dec,
            unit=units,
            frame=frame,
            name=name
        )
    )


def to_dishconfiguration(dish_configuration: DishConfiguration) -> cdm_DishConfiguration:
    pdm_rx = dish_configuration.receiver_band
    LOG.info(f'Setting CDM dish configuration: {pdm_rx}')
    return cdm_DishConfiguration(
        receiver_band=cdm_ReceiverBand(pdm_rx.value)
    )


def to_sdpconfiguration(scan_definition: ScanDefinition):
    scan_type = scan_definition.scan_type_id
    LOG.info(f'Setting SDP scan configuration: {scan_type}')
    return cdm_SDPConfiguration(
        scan_type=scan_type
    )