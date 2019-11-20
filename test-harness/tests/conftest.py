import os
import pytest

from collections import namedtuple

"""
RunContext is a metadata object to access values from the environment, 
i.e. data that is injected in by the Makefile. Useful if tests need to 
be aware of the k8s context they are running in, such as the HELM_RELEASE.

This will allow tests to resolve hostnames and other dynamic properties.

Example:

def test_something(run_context):
    HOSTNAME = 'some-pod-{}'.format(run_context.HELM_RELEASE)

"""
@pytest.fixture(scope="session")
def run_context():
    ENV_VARS = ['HELM_RELEASE'] # list of required environment vars

    RunContext = namedtuple('RunContext', ENV_VARS)
    values = list()

    for var in ENV_VARS:
        assert os.environ.get(var) # all ENV_VARS must have values set
        values.append(os.environ.get(var))

    return RunContext(*values)

