import pytest
from pytest_bdd import scenario


@pytest.mark.skalow
@pytest.mark.scan
@pytest.mark.csp
@scenario("features/csp_abort_scanning.feature", "Abort scanning on CSP Low")
def test_abort_scanning_on_low_csp(disable_clear):
    """Abort in scanning obstate."""
