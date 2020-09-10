#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-1080
"""

import logging
import pytest
from functools import partial
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then, parsers
from tango import DeviceProxy
from resources.test_support.helpers import resource, watch


LOGGER = logging.getLogger(__name__)

@pytest.mark.fast
@scenario("XTP-1080.feature", "Executing a new transaction")
def test_execute_new_txn(command_name):
    pass


@given("an example transaction logging application")
def logging_transaction_application():
    pass


@given("a transaction ID is not present")
def transaction_id():
    pass

@when(parsers.parse("executing a transaction named <command_name>"))
def execute_txn(command_name):
    pass


@then("a new transaction ID is generated")
def check_generate_txn_id():
    pass


@then(parsers.parse("start of transaction is logged including that transaction ID and name <command_name>" ))
def check_start_log():
    pass


@then(parsers.parse("end of transaction is logged including that transaction ID and name <command_name>"))
def check_end_log():
    assert 1

