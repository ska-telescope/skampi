import pytest
from pytest_bdd import scenario


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.configure

@scenario("features/sdp_abort_configuring.feature", "Abort configuring SDP Low")
def test_abort_configuring_on_low_sdp():
    """Abort in configuring obstate."""
