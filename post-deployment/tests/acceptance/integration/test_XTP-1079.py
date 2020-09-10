# coding=utf-8
"""Transaction ID logging feature tests."""
import json
import logging
import pytest

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

import ska.logging


# set up SKA logging immediately
ska.logging.configure_logging()


START_OF_TRANSACTION_LOG_PHRASE = "Start Transaction (ID:"
END_OF_TRANSACTION_LOG_PHRASE = "End Transaction (ID:"
FAILED_TRANSACTION_LOG_PHRASE = "Failed Transaction (ID:"


_existing_transaction_id = None
_generated_transaction_id = None
_params = {}


def command(name, parameter_json, raise_exception=False):
    parameters = json.loads(parameter_json)
    try:
        # FIXME:  Remove temporary implementation!
        transaction_id = parameters.get("transaction_id", "12345")
        logging.info(f"Start Transaction (ID:{transaction_id}, name:{name})")
        if raise_exception:
            raise RuntimeError(f"{FAILED_TRANSACTION_LOG_PHRASE}{transaction_id}, name:{name})")
        logging.info(f"Dummy message in transaction")
        logging.info(f"End Transaction (ID:{transaction_id}, name:{name})")
        # with ska.logging.transaction(name, parameters) as transaction_id:
        #     if raise_exception:
        #         raise RuntimeError("Command Failed!!!")
    except RuntimeError:
        # FIXME: Remove this temporary log - expect context handler to do it
        logging.exception("Temporary log")
        logging.info(f"End Transaction (ID:{transaction_id}, name:{name})")
    else:
        assert not raise_exception, "Expected RuntimeError to be raised."

    return transaction_id


@pytest.fixture
def existing_transaction_id():
    return _existing_transaction_id


@pytest.fixture
def generated_transaction_id():
    return _generated_transaction_id


@pytest.fixture
def params(existing_transaction_id):
    if existing_transaction_id:
        _params['transaction_id'] = existing_transaction_id
    else:
        _params.pop('transaction_id', None)

    return _params


@pytest.mark.karoo
@scenario('XTP-1079.feature', 'Continuing an existing transaction')
def test_continuing_an_existing_transaction():
    pass


@pytest.mark.karoo
@scenario('XTP-1079.feature', 'Executing a new transaction')
def test_executing_a_new_transaction():
    pass


@pytest.mark.karoo
@scenario('XTP-1079.feature', 'Executing a transaction that fails')
def test_executing_a_transaction_that_fails():
    pass


# @pytest.mark.karoo
@scenario('XTP-1079.feature', 'Executing a transaction with parameters')
def test_executing_a_transaction_with_parameters():
    pass


@given('an example transaction logging application')
def an_example_transaction_logging_application():
    pass


@given('a transaction ID is already present')
def a_transaction_id_is_already_present():
    global _existing_transaction_id  # not pretty...
    _existing_transaction_id = "12345-badE"


@given('a transaction ID is not present')
def a_transaction_id_is_not_present():
    global _existing_transaction_id  # not pretty...
    _existing_transaction_id = None


@given('the transaction parameters are <parameters>')
def the_transaction_parameters_are_parameters(parameters):
    global _params  # not pretty...
    _params = json.loads(parameters)


@when('executing a transaction named <command_name>')
def executing_a_transaction(command_name, params):
    params_json = json.dumps(params)
    global _generated_transaction_id  # not pretty...
    _generated_transaction_id = command(command_name, params_json)


@when('executing a failed transaction named <command_name>')
def executing_a_failed_transaction(command_name, params):
    params_json = json.dumps(params)
    global _generated_transaction_id  # not pretty...
    _generated_transaction_id = command(command_name, params_json, raise_exception=True)


@then('a new transaction ID is generated')
def a_new_transaction_id_is_generated(existing_transaction_id, generated_transaction_id):
    assert generated_transaction_id != existing_transaction_id
    assert generated_transaction_id is not None


@then('that transaction ID is used')
def that_transaction_id_is_used(existing_transaction_id, generated_transaction_id):
    assert generated_transaction_id == existing_transaction_id
    assert generated_transaction_id is not None


@then('start of transaction is logged including that transaction ID and name <command_name>')
def start_of_transaction_is_logged_ignore_parameters(generated_transaction_id, command_name, caplog):
    assert check_logs([START_OF_TRANSACTION_LOG_PHRASE, generated_transaction_id, command_name], caplog), f"Logs {caplog.text.splitlines()}"


@then('start of transaction is logged including that transaction ID and name <command_name> and <parameters>')
def start_of_transaction_is_logged_check_parameters(generated_transaction_id, command_name, parameters, caplog):
    assert check_logs([START_OF_TRANSACTION_LOG_PHRASE, generated_transaction_id, command_name, parameters], caplog), f"Logs {caplog.text.splitlines()}"


@then('end of transaction is logged including that transaction ID and name <command_name>')
def end_of_transaction_is_logged_ignore_parameters(generated_transaction_id, command_name, caplog):
    assert check_logs([END_OF_TRANSACTION_LOG_PHRASE, generated_transaction_id, command_name], caplog), f"Logs {caplog.text.splitlines()}"


@then('failed transaction is logged including that transaction ID and name <command_name>')
def failed_transaction_is_logged_check_error_message(generated_transaction_id, command_name, caplog):
    assert check_logs([FAILED_TRANSACTION_LOG_PHRASE, generated_transaction_id, command_name], caplog), f"Logs {caplog.text.splitlines()}"

def check_logs(items_to_find_in_line, caplog):
    """Goes through all the lines that caplog captured and 
       checks whether all the are in a line
    """
    for record in caplog.text.splitlines():
        if all([True if item in record else False for item in items_to_find_in_line]):
            return True
    return False
