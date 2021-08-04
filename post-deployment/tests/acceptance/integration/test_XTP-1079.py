# coding=utf-8
"""Transaction ID logging feature tests."""

import pytest
import random
import string
import logging
import json

import ska_ser_logging

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

from ska_ser_log_transactions import transaction

# Configure SKA logging immediately when tests start
ska_ser_logging.configure_logging()
logger = logging.getLogger("ska.test.XTP-1079")


START_OF_TRANSACTION_LOG_PHRASE = "Enter["
END_OF_TRANSACTION_LOG_PHRASE = "Exit["
FAILED_TRANSACTION_LOG_PHRASE = "Exception["


class ExampleApplication:
    def __init__(self):
        self.transaction_id = None

    def execute(
        self, name, parameter_json, raise_exception=False, transaction_id="", transaction_id_key="",
    ):
        parameters = json.loads(parameter_json)
        try:
            if transaction_id_key:
                with transaction(
                    name,
                    parameters,
                    transaction_id=transaction_id,
                    transaction_id_key=transaction_id_key,
                ) as transaction_id:
                    logger.info("Dummy log inside transaction")
                    if raise_exception:
                        raise RuntimeError("Command Failed!!!")
            else:
                with transaction(
                    name, parameters, transaction_id=transaction_id
                ) as transaction_id:
                    logger.info("Dummy log inside transaction")
                    if raise_exception:
                        raise RuntimeError("Command Failed!!!")
        except RuntimeError:
            pass
        else:
            assert not raise_exception, "Expected RuntimeError propogate out of context handler."

        self.transaction_id = transaction_id

    def new_transaction_id(self):
        return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


@pytest.mark.xfail
@pytest.mark.skamid
@scenario("XTP-1079.feature", "Executing a transaction that fails")
def test_executing_a_transaction_that_fails():
    pass


@pytest.mark.xfail
@scenario("XTP-1079.feature", "Executing a transaction that succeeds")
def test_executing_a_transaction_that_succeeds():
    pass


@given("an example transaction logging application")
def example_app():
    return ExampleApplication()


@when(
    "executing a successful transaction named <command_name> with <parameters> and <transaction_id> and <transaction_id_key>"
)
def executing_a_successful_transaction(
    example_app, command_name, parameters, transaction_id, transaction_id_key
):
    example_app.execute(
        command_name,
        parameters,
        transaction_id=transaction_id,
        transaction_id_key=transaction_id_key,
    )


@when(
    "executing a transaction named <command_name> with <parameters> and <transaction_id> and <transaction_id_key> that raises an exception"
)
def executing_a_failed_transaction(
    example_app, command_name, parameters, transaction_id, transaction_id_key
):
    example_app.execute(
        command_name,
        parameters,
        raise_exception=True,
        transaction_id=transaction_id,
        transaction_id_key=transaction_id_key,
    )


@then(
    "the start of the transaction is logged with the <expected_transaction_id>, <command_name> and <parameters>"
)
def check_start_of_the_transaction_is_logged(
    example_app, expected_transaction_id, command_name, parameters, caplog
):
    if expected_transaction_id == "< newly_generated >":
        expected_transaction_id = example_app.transaction_id
    assert check_logs(
        [START_OF_TRANSACTION_LOG_PHRASE, expected_transaction_id, command_name, parameters,],
        caplog,
    )


@then("the end of the transaction is logged with the <expected_transaction_id> and <command_name>")
def check_end_of_the_transaction_is_logged(
    example_app, expected_transaction_id, command_name, caplog
):
    if expected_transaction_id == "< newly_generated >":
        expected_transaction_id = example_app.transaction_id
    assert check_logs(
        [END_OF_TRANSACTION_LOG_PHRASE, expected_transaction_id, command_name], caplog
    )


@then("the exception message is logged with the <expected_transaction_id> and <command_name>")
def check_exception_message_is_logged(example_app, expected_transaction_id, command_name, caplog):
    if expected_transaction_id == "< newly_generated >":
        expected_transaction_id = example_app.transaction_id
    assert check_logs(
        [FAILED_TRANSACTION_LOG_PHRASE, expected_transaction_id, command_name], caplog
    )


def check_logs(items_to_find_in_line, caplog):
    """Verify that all items occur in at least one log line."""
    for record in caplog.text.splitlines():
        if all([True if item in record else False for item in items_to_find_in_line]):
            return True
    return False
