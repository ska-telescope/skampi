import pytest
import logging
from pytest_bdd import scenario, given, when, then, parsers

@pytest.mark.karoo
@scenario("XTP-1079.feature", "Executing a new transaction")
def test_new_transaction():
    pass

@given("an example transaction logging application")
def example_app():
    return "I am example app"

@when("executing a transaction")
def transaction(example_app):
    logging.info(f"{example_app}")

@when("no transaction ID is present")
def nothing():
    pass
