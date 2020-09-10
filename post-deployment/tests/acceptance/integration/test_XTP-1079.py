# coding=utf-8
"""Transaction ID logging feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


@scenario('XTP-1079.feature', 'Continuing an existing transaction')
def test_continuing_an_existing_transaction():
    """Continuing an existing transaction."""


@scenario('XTP-1079.feature', 'Executing a new transaction')
def test_executing_a_new_transaction():
    """Executing a new transaction."""


@scenario('XTP-1079.feature', 'Executing a transaction that fails')
def test_executing_a_transaction_that_fails():
    """Executing a transaction that fails."""


@scenario('XTP-1079.feature', 'Executing a transaction with parameters')
def test_executing_a_transaction_with_parameters():
    """Executing a transaction with parameters."""


@given('a transaction ID is already present')
def a_transaction_id_is_already_present():
    """a transaction ID is already present."""
    raise NotImplementedError


@given('a transaction ID is not present')
def a_transaction_id_is_not_present():
    """a transaction ID is not present."""
    raise NotImplementedError


@given('an example transaction logging application')
def an_example_transaction_logging_application():
    """an example transaction logging application."""
    raise NotImplementedError


@given('the transaction parameters are <parameters>')
def the_transaction_parameters_are_parameters():
    """the transaction parameters are <parameters>."""
    raise NotImplementedError


@when('an exception occurs')
def an_exception_occurs():
    """an exception occurs."""
    raise NotImplementedError


@when('executing a transaction named <command_name>')
def executing_a_transaction_named_command_name():
    """executing a transaction named <command_name>."""
    raise NotImplementedError


@then('a new transaction ID is generated')
def a_new_transaction_id_is_generated():
    """a new transaction ID is generated."""
    raise NotImplementedError


@then('end of transaction is logged including that transaction ID and name <command_name>')
def end_of_transaction_is_logged_including_that_transaction_id_and_name_command_name():
    """end of transaction is logged including that transaction ID and name <command_name>."""
    raise NotImplementedError


@then('end of transaction is logged including that transaction ID and name <command_name> and the error message')
def end_of_transaction_is_logged_including_that_transaction_id_and_name_command_name_and_the_error_message():
    """end of transaction is logged including that transaction ID and name <command_name> and the error message."""
    raise NotImplementedError


@then('start of transaction is logged including that transaction ID and name <command_name>')
def start_of_transaction_is_logged_including_that_transaction_id_and_name_command_name():
    """start of transaction is logged including that transaction ID and name <command_name>."""
    raise NotImplementedError


@then('start of transaction is logged including that transaction ID and name <command_name> and <parameters>')
def start_of_transaction_is_logged_including_that_transaction_id_and_name_command_name_and_parameters():
    """start of transaction is logged including that transaction ID and name <command_name> and <parameters>."""
    raise NotImplementedError


@then('that transaction ID is used')
def that_transaction_id_is_used():
    """that transaction ID is used."""
    raise NotImplementedError

