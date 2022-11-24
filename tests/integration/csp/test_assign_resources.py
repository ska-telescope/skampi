"""Assign resources to subarray feature tests."""
import logging
from typing import Any

import pytest
from pytest_bdd import scenario, then
from ..conftest import ObservationConfigInterjector, Observation
from resources.models.obsconfig.base import EncodedObject

logger = logging.getLogger(__name__)


@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Assign resources to CSP low subarray",
)
def test_assign_resources_to_csp_low_subarray():
    """Assign resources to CSP low subarray."""


@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Assign resources to CSP mid subarray",
)
def test_assign_resources_to_csp_mid_subarray():
    """Assign resources to CSP mid subarray."""


@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Release resources assigned to an CSP low subarray",
)
def test_release_resources_to_csp_low_subarray():
    """Release resources assigned to an CSP low subarray"""


@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Release resources assigned to an CSP mid subarray",
)
def test_release_resources_to_csp_mid_subarray():
    """Release resources assigned to an CSP mid subarray"""


def generate_invalid_config(observation: Observation):
    # correct_config = observation.generate_assign_resources_config().as_dict
    incorrect_config = {}
    return EncodedObject(incorrect_config)


@pytest.fixture(name="set_obs_config_as_invalid")
def fxt_set_obs_config_as_invalid(
    interject_into_observation_config: ObservationConfigInterjector[
        [], EncodedObject[dict[str, Any]]
    ]
):
    interject_into_observation_config(
        "generate_assign_resources_config", generate_invalid_config
    )


@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Assign resources with invalid config to CSP",
)
def test_assign_resources_with_invalid_config_to_csp():  # type: ignore
    """Assign resources with invalid config to CSP"""


# use when from ..shared_assign_resources in ..conftest.py
# @when("I assign resources to it")

# for release resources test
# use when from ..shared_assign_resources in ..conftest.py
# @when("I release all resources assigned to it")

# mock tests
# TODO
