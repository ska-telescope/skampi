from resources.test_support.subscribing import EventData,MessageBoard,MessageHandler,DeviceProxy,Handling,Tuple,List,SubscriptionId
from collections import namedtuple
from logging import Logger
from contextlib import contextmanager
from tango import DevState, TimeVal
from typing import Callable, ClassVar,Tuple, Set
from functools import partial
from time import sleep

BuildSpec = namedtuple('BuildSpec',['attr','device','handler'])

subarray_devices = [
        'ska_mid/tm_subarray_node/1',
        'mid_csp/elt/subarray_01',
        'mid_csp_cbf/sub_elt/subarray_01',
        'mid_sdp/elt/subarray_1']

### event handlers ###
#NOTE this mechanism sometimes get events from previous subscriptions when there 
# is a very fast turn around, suggest to use this mechansim only at special cases
class WaitUntilEqual(MessageHandler):
    '''
    Handles events generated on a messageboard by checking that for a specific
    device and attribute they have become equal upon which it removes the subscription
    '''

    def __init__(self,board, attr: str, value: str, device: str) -> None:
        super(WaitUntilEqual,self).__init__(board)
        self.attr = attr
        self.device = device
        self.value = value

    def condition_met(self, event) -> bool:
        return (str(event.attr_value.value)== self.value)

    def handle_event(self, event: EventData, id: SubscriptionId, logger) -> None:
        self._print_event(event)
        if self.condition_met(event):
            self.unsubscribe(id)
        super(WaitUntilEqual,self).handle_event(event,id)

    def supress_timeout(self) -> bool:
        return False

class WaitUntilChanged(MessageHandler):
    '''
    Handles events generated on a messageboard by checking that for a specific
    device and attribute whether they have changed (irrespective of the actual value)
    if the condition is met the event is unsubscribed
    '''

    def __init__(self,board,attr: str, device: str) -> None:
        super(WaitUntilChanged,self).__init__(board)
        self.attr = attr
        self.device = device
        self.starting_value = None

    def condition_met(self) -> bool:
        assert self.starting_value is not None
        return self.starting_value != self.current_value

    def update(self,event):
        value = str(event.attr_value.value)
        if self.starting_value is None:
            self.starting_value = value
            self.tracer.message(f'first event received, starting state = {self.starting_value}')
        self.current_value = value

    def handle_event(self, event: EventData, id: SubscriptionId, logger) -> None:
        self._print_event(event)
        self.update(event)
        if self.condition_met():
            self.unsubscribe(id)
            self.base_evaluation_met = True
        super(WaitUntilChanged,self).handle_event(event,id)

class ObserveEvent(MessageHandler):
    '''
    Records the values of events being generated on a specific subscription for diagnostic
    purposes but does not perform any waits on it
    '''
    def __init__(self,board, attr: str, device: str) -> None:
        super(ObserveEvent,self).__init__(board)
        self.attr = attr
        self.device = device
    
    def handle_event(self, event: EventData, id: SubscriptionId,logger) -> None:
        self._print_event(event)
        super(ObserveEvent,self).handle_event(event,id)

    def supress_timeout(self) -> bool:
        return True
    

### builders ###
class ForAttr():
    '''
    intermediate class for buildinng a rule based spec
    takes input device and attribute and returns an condition for evaluating the attribute
    '''
    def __init__(self,attr,device,builder) -> None:
        self.attr = attr
        self.device = device
        self.builder = builder

    def _add_spec(self, handler: MessageHandler) -> BuildSpec:
        spec = BuildSpec(
            self.attr,
            self.device,
            handler
        )
        self.builder.add_spec(spec)
        return spec

    def to_become_equal_to(self,value: str) -> None:
        '''
        adds a spec on the builder by choosing
        a handler for the condition to become equal
        '''
        board = self.builder.board
        handler = WaitUntilEqual(board,self.attr,value,self.device)
        spec = self._add_spec(handler)
        return spec

    def to_change(self) -> None:
        '''
        adds a spec on the builder by choosing
        a handler for the condition to become equal
        '''
        board = self.builder.board
        handler = WaitUntilChanged(board,self.attr, self.device)
        spec = self._add_spec(handler)
        return spec
    
    def and_observe(self):
        '''
        adds a spec on the builder by choosing
        a handler for the condition to become equal
        '''
        board = self.builder.board
        handler = ObserveEvent(board,self.attr, self.device)
        spec = self._add_spec(handler)
        return spec


class SetWatingOn():

    def __init__(self, device: str,builder ) -> None:
        self.device = device
        self.builder = builder

    def for_attribute(self, attr: str):
        return ForAttr(attr,self.device,self.builder)

class MessageBoardBuilder():

    def __init__(self) -> None:
        self.board = MessageBoard()
        self.specs:Set[BuildSpec] = set()

    def set_waiting_on(self,device):
        return SetWatingOn(device,self)

    def add_spec(self, spec: BuildSpec) -> None:
        self.specs.add(spec)

    def setup_board(self):
        for _,spec in enumerate(self.specs):
            handler = spec.handler
            self.board.add_subscription(spec.device,spec.attr,handler)
        return self.board

### rule based pre and post conditions ###
## telescope starting up ##

def set_wating_for_start_up() -> MessageBoardBuilder:
    b = MessageBoardBuilder()
    #b.set_waiting_on('ska_mid/tm_subarray_node/1').for_attribute('State').to_become_equal_to('ON')
    #b.set_waiting_on('mid_csp/elt/subarray_01').for_attribute('State').to_become_equal_to('ON')
    #b.set_waiting_on('mid_csp_cbf/sub_elt/subarray_01').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('mid_csp/elt/master').for_attribute('State').to_become_equal_to('ON')
    # TODO disabled because it does not have polling set up
    #b.set_waiting_on('mid_sdp/elt/master').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('ska_mid/tm_central/central_node').for_attribute('State').to_become_equal_to('ON')
    return b

## telescope shutting down
def set_wating_for_shut_down() -> MessageBoardBuilder:
    b = MessageBoardBuilder()
    b.set_waiting_on('mid_csp/elt/master').for_attribute('State').to_become_equal_to('STANDBY')
    #b.set_waiting_on('mid_csp/elt/subarray_01').for_attribute('State').to_become_equal_to('OFF')
    #b.set_waiting_on('mid_csp_cbf/sub_elt/subarray_01').for_attribute('State').to_become_equal_to('OFF')
    # TODO disabled because it does not have polling set up
    # b.set_waiting_on('mid_sdp/elt/master').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('ska_mid/tm_central/central_node').for_attribute('State').to_become_equal_to('OFF')
    return b
    
## generic helpers for context managers and sync
def wait(board:MessageBoard, timeout: float, logger: Logger):
    print_message = ''
    for item in board.get_items(timeout):
        event,id,handler = (item.event,item.subscription,item.handler)
        handler.handle_event(event,id,logger)
        print_message = f'{print_message}{handler.print_event(event)}'
    logger.info(print_message)

### context managers and decorators for using rule based pre/post control

## checks ##
def check_coming_out_of_standby():
    pass

def check_going_into_standby():
    pass

# telescope starting up
@contextmanager
def sync_telescope_starting_up(logger,timeout=5):
    check_coming_out_of_standby()
    builder = set_wating_for_start_up()
    board = builder.setup_board()
    yield
    wait(board,timeout,logger)
    logger.info(board.replay_subscriptions())  


# telescope shutting down
@contextmanager
def sync_telescope_shutting_down(logger,timeout=5):
    check_going_into_standby()
    builder = set_wating_for_shut_down()
    board = builder.setup_board()
    yield
    wait(board,timeout,logger)

watchSpec = namedtuple('watchSpec',['device','attr'])
@contextmanager
def observe_states(specs:List[Tuple[str,str]],logger,timeout=5):
    b = MessageBoardBuilder()
    for spec in  specs:
        b.set_waiting_on(spec.device).for_attribute(spec.attr).and_observe()
    board = b.setup_board()
    yield
    wait(board,timeout,logger)
    logger.info(board.replay_subscriptions())   



  

   



        
        


    
