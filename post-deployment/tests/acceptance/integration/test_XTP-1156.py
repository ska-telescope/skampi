#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-1156
----------------------------------
Test that the  OET `create` command fails when given a file that does not exist with expected
message and status code.
"""

import pytest
from pytest_bdd import given, scenario, then, when, parsers
import subprocess
import os

OET_ENV = os.environ.copy()
HELM_RELEASE = OET_ENV.get("HELM_RELEASE", "test")
OET_ENV["OET_REST_URI"] = f"http://oet-rest-{HELM_RELEASE}:5000/api/v1.0/procedures"


@pytest.mark.fast
@pytest.mark.common
@scenario("XTP-1156.feature", "Observation Execution Tool")
def test_create():
    pass


@given('The Observation Execution Tool create command')
def command():
    pass


@when('OET create is given a <file> that does not exist')
def output_from_junk_file(file):
    result = subprocess.run(['oet', 'create', file], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=OET_ENV)
    output = ''.join(result.stdout.decode('utf-8') + result.stderr.decode('utf-8'))
    return output


@then("the OET returns an <error>")
def oet_return_error_for_garbage_file(file, error):

    assert output_from_junk_file(file).count(error) > 0
