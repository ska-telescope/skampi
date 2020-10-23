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


@pytest.mark.fast
@scenario("XTP-1156.feature", "Observation Execution Tool")
def test_create():
    pass


@given('The Observation Execution Tool create command')
def command():
    pass


@when('OET create is given a <file> that does not exist')
def output_from_junk_file(file):
    result = subprocess.run(['oet', 'create', file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = ''.join(result.stdout.decode('utf-8') + result.stderr.decode('utf-8'))
    return output


@then("the OET returns an <error>")
def oet_return_error_for_garbage_file(file, error):

    assert output_from_junk_file(file).count(error) > 0
