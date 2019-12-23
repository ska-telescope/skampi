import pytest

from tests.testsupport.helm import HelmTestAdaptor


def pytest_addoption(parser):
    parser.addoption(
        "--use-tiller-plugin", action="store_true", default=False, help="Wraps helm commands in `helm tiller run --`."
    )


@pytest.fixture(scope="session")
def helm_adaptor(pytestconfig):
    return HelmTestAdaptor(pytestconfig.getoption("--use-tiller-plugin"))