"""Configure an EDA database instance for Mid"""
import logging
import os
import time
import httpx
import psycopg2
import pytest
import yaml
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from tests.integration.archiver.archiver_helper import ArchiverHelper
from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)
# log capturing


DB_NAME = os.getenv("ARCHIVER_DBNAME")
DB_USER = os.getenv("ARCHIVER_DB_USER")
DB_PASS = os.getenv("ARCHIVER_DB_PWD")
DB_PORT = os.getenv("ARCHIVER_PORT")
KUBE_NAMESPACE = os.getenv("KUBE_NAMESPACE")
CONFIG = os.getenv("CONFIG")

EVENT_SUBSCRIBER = f"{CONFIG}-eda/es/01"
CONFIGURATION_MANAGER = f"{CONFIG}-eda/cm/01"
DB_HOST = f"timescaledb.ska-eda-{CONFIG}-db.svc.cluster.local"
TANGO_DATABASE_DS = "databaseds-tango-base"
archiver_helper = ArchiverHelper(CONFIGURATION_MANAGER, EVENT_SUBSCRIBER)

@pytest.mark.skip(reason="Raised bug SKB-226")
@pytest.mark.eda
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@scenario("features/archiver.feature", "Configure an EDA database instance for Mid")
def test_archiver_configuration_in_mid():
    """Configure an EDA database instance for Mid"""


@pytest.mark.skip(reason="Raised bug SKB-226")
@pytest.mark.eda
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@scenario("features/archiver.feature", "Archive an change event on EDA database instance for Mid")
def test_archiver_in_mid():
    """Archive an change event on EDA database instance for Mid"""

@pytest.mark.edalow
@pytest.mark.eda
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@scenario("features/archiver.feature", "Configure an EDA database instance for Low")
def test_archiver_configuration_in_low():
    """Configure an EDA database instance for Low"""

@pytest.mark.edalow
@pytest.mark.eda
@pytest.mark.k8s
@pytest.mark.k8sonly
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


@given("an EDA archive configuration file specifying subarray obsstate to be archived")
def configuration_file():

    with open(
        "tests/integration/archiver/config_file/subarray_obsState.yaml", "r+", encoding="UTF-8"
    ) as stream:
        data = yaml.load(stream, Loader=yaml.Loader)
        data["db"] = f"databaseds-tango-base.{KUBE_NAMESPACE}.svc.cluster.local:10000"
        data["archiver"] = EVENT_SUBSCRIBER
        data["manager"] = CONFIGURATION_MANAGER
        config = CONFIG.capitalize()
        data["configuration"][0]["class"] = f"SubarrayNode{config}"

    with open(
        "tests/integration/archiver/config_file/subarray_obsState.yaml", "w", encoding="utf-8"
    ) as conf_stream:
        conf_stream.write(yaml.dump(data, sort_keys=False))


@given("an telescope subarray", target_fixture="composition")
def an_telescope_subarray(
    set_up_subarray_log_checking_for_tmc,
    base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """
    an telescope subarray.

    :param set_tmc_entry_point: To set up subarray log checking for tmc.
    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition

def check_obsstate_attribute():
    try:
        eda_es = con_config.get_device_proxy(EVENT_SUBSCRIBER)
        
        while True:
            attribute_list = eda_es.read_attribute("AttributeList")
            logger.info(f"Attribute list: {attribute_list.value}")
            
            target_substring = "/tm_subarray_node/1/obsstate"
            if any(target_substring in attribute for attribute in attribute_list.value):
                return True
            
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False
    
@given("a EDA database instance configured to archive an change event on the subarray obsstate")
@when("I upload the configuration file")
def configure_archiver():
    eda_es = con_config.get_device_proxy(EVENT_SUBSCRIBER)
    with open("tests/integration/archiver/config_file/subarray_obsState.yaml", "rb") as file:
        response = httpx.post(
            f"http://configurator.{KUBE_NAMESPACE}.svc.cluster.local:8003/configure-archiver",
            files={"file": ("subarray_obsState.yaml", file, "application/x-yaml")},
            data={"option": "add_update"},
            timeout=None,
        )
    check_obsstate_attribute()
    assert response.status_code == 200
    status = eda_es.command_inout("AttributeStatus", f"ska_{CONFIG}/tm_subarray_node/1/obsstate")
    event_count = int(status.split("Started\nEvent OK counter   :")[1].split("-")[0])
    assert event_count == 1

# @when("I assign resources to the subarray") from conftest


@then("the subarray went to obststate to IDLE event must be archived")
def check_archived_attribute(sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings
    ):
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)
    eda_es = con_config.get_device_proxy(EVENT_SUBSCRIBER)
    status = eda_es.command_inout("AttributeStatus", f"ska_{CONFIG}/tm_subarray_node/1/obsstate")
    event_count = int(status.split("Started\nEvent OK counter   :")[1].split("-")[0])
    assert event_count > 1

    # teardown
    with open("tests/integration/archiver/config_file/subarray_obsState.yaml", "rb") as file:
        response = httpx.post(
            f"http://configurator.{KUBE_NAMESPACE}.svc.cluster.local:8003/configure-archiver",
            files={"file": ("subarray_obsState.yaml", file, "application/x-yaml")},
            data={"option": "remove"},
            timeout=None,
        )
    context_monitoring.wait_for(EVENT_SUBSCRIBER).for_attribute("AttributeNumber").to_become_equal_to(
        "0", settings=integration_test_exec_settings
    )

    assert response.status_code == 200

    # check obsState IDLE in database
    conn = psycopg2.connect(
        database=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )

    cur = conn.cursor()
    query = f"select value_r_label from att_scalar_devenum where \
    att_conf_id = (select att_conf_id from att_conf where \
    att_name like\
    '%tango://{TANGO_DATABASE_DS}.{KUBE_NAMESPACE}.svc.cluster.local:10000/ska_{CONFIG}/tm_subarray_node/1/obsstate%')\
    order by data_time desc limit 1;"
    cur.execute(query)
    result = cur.fetchall()
    assert result[0][0] == "IDLE"
    conn.close()
