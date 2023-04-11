import pytest
from pytest_bdd import scenario


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.scan
@scenario("features/csp_abort_scanning.feature", "Abort scanning on CSP Low")
def test_abort_scanning_on_low_csp():
    """Abort in scanning obstate."""
