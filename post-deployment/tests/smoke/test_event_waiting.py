from collections import namedtuple

from _pytest.fixtures import fixture
import resources.test_support.event_waiting as sut
import mock
import pytest
from assertpy import assert_that
from functools import reduce

# fixtures as scenarios
class Fxt():

    def __init__(self,
                handler: sut.MessageHandler,
                mock_event: sut.EventData,
                mock_subscription: sut.Subscription,
                mock_logger: sut.Logger,
                mock_board: sut.MessageBoard
                ) -> None:
        self.handler = handler
        self.mock_event = mock_event
        self.mock_subscription = mock_subscription
        self.mock_logger = mock_logger
        self.mock_board = mock_board

@pytest.fixture
def fxt_configured_subscription_with_event() -> Fxt:
    # given an incoming event
    mock_event = mock.Mock(sut.EventData)
    # with attr_value = '1st event'
    mock_event.attr_value.value = '1st event'
    mock_event.err = False
    # resulting from a subscription
    mock_subscription = mock.Mock(sut.Subscription)
    mock_subscription.describe.return_value = ('dummy','dummy',0)
    # configured onto a messageboard
    mock_board = mock.Mock(sut.MessageBoard)
    # and a control loop with a logger
    mock_logger = mock.Mock(sut.Logger)
    fxt = Fxt(
        None,
        mock_event,
        mock_subscription,
        mock_logger,
        mock_board
    )
    yield fxt

@pytest.fixture
def fxt_configured_wait_until_changed(fxt_configured_subscription_with_event) -> Fxt:
    # given an incoming event
    # with attr_value = '1st event'
    # resulting from a subscription
    # configured onto a messageboard
    # and a control loop with a logger
    fxt = fxt_configured_subscription_with_event
    # when I handle this event with a WaitUntilEqual handler
    # that is configured on a message board to wait for a dummy device with 
    # dummy attr to become equal to value 'desired value"
    fxt.handler = sut.WaitUntilEqual(
        fxt.mock_board,
        'dummy attr',
        'desired value',
        'dummy device'
    )
    yield fxt


@pytest.fixture
def fxt_1st_event_on_wait_until_changed(fxt_configured_wait_until_changed) -> Fxt:
    # given an incoming event
    # with attr_value = '1st event'
    # resulting from a subscription
    # and a control loop with a logger
    # when I handle this event with a WaitUntilEqual handler
    # that is configured on a message board to wait for a dummy device with 
    # dummy attr to become equal to value 'desired value"
    fxt = fxt_configured_wait_until_changed
    # and for which the first event has already been called
    fxt.handler.handle_event(
        fxt.mock_event,
        fxt.mock_subscription,
        fxt.mock_logger)
    yield fxt
    

@pytest.mark.skamid
def test_handler_waitUntilEqual_not_called(fxt_configured_wait_until_changed):
    # given an incoming event
    # with attr_value = '1st event'
    # resulting from a subscription
    # and a control loop with a logger
    # when I handle this event with a WaitUntilEqual handler
    # that is configured on a message board to wait for a dummy device with 
    # dummy attr to become equal to value 'desired value"
    fxt = fxt_configured_wait_until_changed
    # then when I call the handler to handle given event
    fxt.handler.handle_event(
        fxt.mock_event,
        fxt.mock_subscription,
        fxt.mock_logger)
    # I expect the subscription not to be removed
    fxt.mock_board.remove_subscription.assert_not_called()

@pytest.mark.skamid
def test_handler_waitUntilEqual_called_when_changed(fxt_1st_event_on_wait_until_changed):
    # given an incoming event
    # with attr_value = '1st event'
    # resulting from a subscription
    # and a control loop with a logger
    # when I handle this event with a WaitUntilEqual handler
    # that is configured on a message board to wait for a dummy device with 
    # dummy attr to become equal to value 'desired value"
    # and for which the first event has already been called
    fxt = fxt_1st_event_on_wait_until_changed
    # then when I call the handler to handle with a new event = desired value
    fxt.mock_event.attr_value.value = 'desired value'
    fxt.handler.handle_event(
        fxt.mock_event,
        fxt.mock_subscription,
        fxt.mock_logger)
    # I expect the subscription to be removed
    fxt.mock_board.remove_subscription.assert_called_with(fxt.mock_subscription)

@pytest.mark.skamid
def test_handler_waitUntilEqual_remove_when_master(fxt_1st_event_on_wait_until_changed):
    # given an incoming event
    # with attr_value = '1st event'
    # resulting from a subscription
    # and a control loop with a logger
    # when I handle this event with a WaitUntilEqual handler
    # that is configured on a message board to wait for a dummy device with 
    # dummy attr to become equal to value 'desired value"
    # and for which the first event has already been called
    fxt = fxt_1st_event_on_wait_until_changed
    # and for which the handler has been configured as master
    fxt.handler.master = True
    # then when I call the handler to handle with a new event = desired value
    fxt.mock_event.attr_value.value = 'desired value'
    fxt.handler.handle_event(
        fxt.mock_event,
        fxt.mock_subscription,
        fxt.mock_logger)
    # I expect the subscription to be removed
    fxt.mock_board.remove_subscription.assert_called_with(fxt.mock_subscription)
    # and I also expect all subscriptions to be removed on the board
    fxt.mock_board.remove_all_subcriptions.assert_called()

@pytest.mark.skamid
def test_observe_handler(fxt_configured_subscription_with_event):
    # given an incoming event
    # with attr_value = '1st event'
    # resulting from a subscription
    # configured onto a messageboard
    # and a control loop with a logger
    fxt: Fxt = fxt_configured_subscription_with_event
    # and an event handler ObserveEvent
    fxt.handler = sut.ObserveEvent(
        fxt.mock_board,
        'dummy',
        'dummy'
    )
    # then when I call the handler to handle given event
    fxt.handler.handle_event(
        fxt.mock_event,
        fxt.mock_subscription,
        fxt.mock_logger)
    # I expect the message to be logged in its internal tracer
    # with at least the value of the event
    tracer_message_strings_as_list = [m.message for m in fxt.handler.tracer.messages]
    tracer_message_strings = reduce(lambda x,y: f'{x} {y}',tracer_message_strings_as_list)
    assert_that(tracer_message_strings).contains('1st event')

    



