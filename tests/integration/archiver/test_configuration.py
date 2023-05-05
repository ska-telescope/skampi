"""Configure an EDA database instance for Mid"""
import logging
import yaml, os
import httpx
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then , when
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ..conftest import SutTestSettings


logger = logging.getLogger(__name__)

# log capturing

CONFIG = os.getenv("CONFIG")
EVENT_SUBSCRIBER= f"{CONFIG}-eda/es/01"
CONFIGURATION_MANAGER = f"{CONFIG}-eda/cm/01"
KUBE_NAMESPACE =  os.getenv("KUBE_NAMESPACE")
INITIAL_LEN = 0

print(EVENT_SUBSCRIBER)

@pytest.mark.k8s
@pytest.mark.skamid
@scenario("features/archiver.feature", "Configure an EDA database instance for Mid")
def test_archiver_configuration_in_mid():
    """Configure an EDA database instance for Mid"""


@pytest.mark.k8s
@pytest.mark.skamid
@scenario("features/archiver.feature", "Archive an change event on EDA database instance for Mid")
def test_archiver_in_mid():
    """Archive an change event on EDA database instance for Mid"""


@pytest.mark.k8s
@pytest.mark.skalow
@scenario("features/archiver.feature", "Configure an EDA database instance for Low")
def test_archiver_configuration_in_low():
    """Configure an EDA database instance for Low"""


@pytest.mark.k8s
@pytest.mark.skalow
@scenario("features/archiver.feature", "Archive an change event on EDA database instance for Low")
def test_archiver_in_low():
    """Archive an change event on EDA database instance for Low"""

@given("a EDA database instance")
def check_eda_instance():
    pass

@given("an EDA configuration service")
def check_eda_service():
    eda_es = con_config.get_device_proxy(EVENT_SUBSCRIBER)
    assert eda_es.ping() > 0
    eda_cm = con_config.get_device_proxy(CONFIGURATION_MANAGER)
    assert eda_cm.ping() > 0

@given("am EDA archive configuration file specifying subarray obsstate to be archived")
def configuration_file():
    
    with open("tests/integration/archiver/config_file/subarray_obsState.yaml", "r+", encoding="UTF-8") as stream:
        data = yaml.load(stream, Loader=yaml.Loader)
        data['db']=f'databaseds-tango-base.{KUBE_NAMESPACE}.svc.cluster.local:10000'
        data["archiver"] = EVENT_SUBSCRIBER
        data['manager'] = CONFIGURATION_MANAGER
        
    with open("tests/integration/archiver/config_file/subarray_obsState.yaml", "w", encoding="utf-8") as conf_stream:
        conf_stream.write(yaml.dump(data, sort_keys=False))
    


@given("an telescope subarray", target_fixture="composition")
def an_telescope_subarray(
    set_up_subarray_log_checking_for_tmc,
    base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """
    an telescope subarray.

    :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition


@given("a EDA database instance configured to archive an change event on the subarray obsstate")
@when("I upload the configuration file")
def configure_archiver():
    eda_es = con_config.get_device_proxy(EVENT_SUBSCRIBER)
    with open(f"tests/integration/archiver/config_file/subarray_obsState.yaml", "rb") as file:
        response = httpx.post(
            f"http://configurator.{KUBE_NAMESPACE}.svc.cluster.local:8003/configure-archiver",
            files={"file": ("subarray_obsState.yaml", file, "application/x-yaml")},
            data={"option": "add_update"},
            timeout=None
        )
    assert response.status_code == 200
    status = eda_es.command_inout("AttributeStatus",'ska_mid/tm_subarray_node/1/obsstate')
    INITIAL_LEN  = int(status.split("Started\nEvent OK counter   :")[1].split("-")[0])
    assert INITIAL_LEN  == 1
        


#@when("I assign resources to the subarray") from conftest

@then("the subarray went to obststate to IDLE event must be archived")
def check_archived_attribute(sut_settings):
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)
    eda_es = con_config.get_device_proxy(EVENT_SUBSCRIBER)
    status = eda_es.command_inout("AttributeStatus",'ska_mid/tm_subarray_node/1/obsstate')
    final_len = int(status.split("Started\nEvent OK counter   :")[1].split("-")[0])
    print(final_len)
    assert final_len > INITIAL_LEN  
    