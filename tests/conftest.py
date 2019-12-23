import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--use-tiller-plugin", action="store_true", default=False, help="Wraps helm commands in `helm tiller run --`."
    )

