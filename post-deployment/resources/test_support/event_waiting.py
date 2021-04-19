import logging
from resources.test_support.subscribing import EventData,MessageBoard,MessageHandler,Tuple,List,Subscription,EventTimedOut
from collections import namedtuple
from logging import Logger
from contextlib import contextmanager
from tango import DevState, TimeVal
from typing import Callable, ClassVar,Tuple, Set
from functools import partial
from time import sleep, time
from concurrent import futures

BuildSpec = namedtuple('BuildSpec',['attr','device','handler','polling'])


master_devices = {"mid_csp_cbf/fsp_corr/01",
        "ska_mid/tm_central/central_node",
        "mid_csp_cbf/sub_elt/master",
        "mid_csp/elt/master",
        "ska_mid/tm_leaf_node/csp_master",
        "ska_mid/tm_leaf_node/sdp_master",
        "mid_d0002/elt/master",
        "mid_d0003/elt/master",
        "mid_d0001/elt/master",
        "mid_d0004/elt/master",
        "mid_sdp/elt/master"}

subarray1_devices = {"mid_csp_cbf/fspcorrsubarray/01_01",
                    "mid_csp_cbf/fspcorrsubarray/02_01",
                    "mid_csp_cbf/fspcorrsubarray/03_01",
                    "mid_csp_cbf/fspcorrsubarray/04_01",
                    "mid_csp_cbf/sub_elt/subarray_01",
                    "mid_csp/elt/subarray_01",
                    "mid_sdp/elt/subarray_1",
                    "ska_mid/tm_subarray_node/1",
                    "ska_mid/tm_leaf_node/csp_subarray01",
                    "ska_mid/tm_leaf_node/sdp_subarray01"}

### event handlers ###
#NOTE this mechanism sometimes get events from previous subscriptions when there 
# is a very fast turn around, suggest to use this mechansim only at special cases
class WaitUntilEqual(MessageHandler):
    '''
    Handles events generated on a messageboard by checking that for a specific
    device and attribute they have become equal upon which it removes the subscription
    '''

    def __init__(self,board: MessageBoard, attr: str, value: str, device: str,master: bool = False) -> None:
        self.attr = attr
        self.device = device
        self.desired_value = value
        self.events =[]
        self.master = master
        super(WaitUntilEqual,self).__init__(board)
        if self.master:
            self.annotate_print_out = ' (master)'

    def describe_self(self) -> str:
        master_shim = ''
        if self.master:
            master_shim = ' (master)'
        return f'handler that waits for {self.attr} on device {self.device} to be equal to {self.desired_value}{master_shim}'

    def _is_first_element(self) -> bool:
        return len(self.events) == 1

    def condition_met(self) -> bool:
        # always ignore the first event as it gets set on subscription an not on behaviour change
        if self._is_first_element():
            return False
        else:
            event = self.events[-1]
            if event.err:
                # continue wiating if an error event was recieved
                return False
            else:
                current_value = self._get_attr_value_as_str(event.attr_value)
                return (str(current_value)== self.desired_value)

    def update(self, event: EventData) -> None:
        self.events.append(event)
        self.tracer.message(f'new event added to list, current list size is {len(self.events)}')


    def handle_event(self,event: EventData, subscription: Subscription, logger: Logger) -> None:
        with self.handle_context(event,subscription):
            self.update(event)
            if self.condition_met():
                self.unsubscribe(subscription)
                if self.master:
                    # unscubrive any other subscriptions slaved onto this one
                    self.unsubscribe_all()
        
    def supress_timeout(self) -> bool:
        return False

# deprecated as the fist event recieved may sometimes be unreliable
class WaitUntilChanged(MessageHandler):
    '''
    Handles events generated on a messageboard by checking that for a specific
    device and attribute whether they have changed (irrespective of the actual value)
    if the condition is met the event is unsubscribed
    '''

    def __init__(self,board,attr: str, device: str) -> None:
        self.attr = attr
        self.device = device
        self.starting_value = None
        super(WaitUntilChanged,self).__init__(board)

    def describe_self(self) -> str:
        return f'handler that waits for any change on {self.attr} on device {self.device}'

    def condition_met(self) -> bool:
        assert self.starting_value is not None
        return self.starting_value != self.current_value

    def update(self,event: EventData):
        value = self._get_attr_value_as_str(event.attr_value)
        if self.starting_value is None:
            self.starting_value = value
            self.tracer.message(f'first event received, starting state = {self.starting_value}')
        self.current_value = value

    def handle_event(self,event: EventData, subscription: object, logger) -> None:
        with self.handle_context(event,subscription):
            self.update(event)
            if self.condition_met():
                self.unsubscribe(subscription)




class WaitForOrderedChange(WaitUntilEqual):
    '''
    similar ro waitUnitil equal except desired value is now a list or
    ordered states that must be followed
    '''

    def _expected_event(self) -> EventData:
        if not self._is_complete():
            return self.desired_value[0]
        else:
            return "None (all events recieved)"

    def _is_partialy_correct(self) -> bool:
        current_event = self._current_event()
        if not current_event.err:
            current_value = self._get_attr_value_as_str(current_event.attr_value)
            expected_value = self._expected_event()
            if current_value == expected_value:
                self.desired_value.pop(0)
                return True
            else:
                self.tracer.message(f'WARNING: current event has a value:{current_value} different than what is expected: {expected_value}')
        return False
            

    def _is_complete(self) -> bool:
        return len(self.desired_value) == 0
            
    def _current_event(self) -> EventData:
        return self.events[-1]

    def condition_met(self) -> bool:
        # always ignore the first returned event
        if self._is_first_element():
            return False
        if self._is_partialy_correct():
        # e.g. the current event is what it is expected to be
            self.tracer.message(f'current event {self._current_event()} is correct, waiting for {self._expected_event()}')
        if self._is_complete():
        # e.g. the entire sequence is equivalent
            return True
    

class ObserveEvent(MessageHandler):
    '''
    Records the values of events being generated on a specific subscription for diagnostic
    purposes but does not perform any waits on it
    '''
    def __init__(self,board, attr: str, device: str) -> None:
        self.attr = attr
        self.device = device
        super(ObserveEvent,self).__init__(board)

    def describe_self(self) -> str:
        return f'handler that records {self.attr} on device {self.device} and stops after a predefined timeout set on the messageboard'

    def supress_timeout(self) -> bool:
        return True

    def print_event(self,event,ignore_first):
        '''
        set to print out always the first event as this aids in observation
        '''
        super(ObserveEvent,self).print_event(event,False)
    

### builders ###
class ForAttr():
    '''
    intermediate class for buildinng a rule based spec
    takes input device and attribute and returns an condition for evaluating the attribute
    '''
    def __init__(self,attr,device,builder,polling=False) -> None:
        self.attr = attr
        self.device = device
        self.builder = builder
        self.polling = polling

    def _add_spec(self, handler: MessageHandler) -> BuildSpec:
        spec = BuildSpec(
            self.attr,
            self.device,
            handler,
            self.polling
        )
        self.builder.add_spec(spec)
        return spec

    def to_become_equal_to(self,value: str,master=False) -> BuildSpec:
        '''
        adds a spec on the builder by choosing
        a handler for the condition to become equal
        '''
        board = self.builder.board
        handler = WaitUntilEqual(board,self.attr,value,self.device,master)
        spec = self._add_spec(handler)
        return spec

    def to_change(self) -> BuildSpec:
        '''
        adds a spec on the builder by choosing
        a handler for the condition to become equal
        '''
        board = self.builder.board
        handler = WaitUntilChanged(board,self.attr, self.device)
        spec = self._add_spec(handler)
        return spec

    def to_change_in_order(self, order: List,master=False)  -> BuildSpec:
        '''
        adds an ordered list of values to which a particular
        attribute must change before being complete
        '''
        board = self.builder.board
        handler = WaitForOrderedChange(board,self.attr,order,self.device,master)
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

    def for_attribute(self, attr: str,polling=False):
        return ForAttr(attr,self.device,self.builder,polling)

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
            polling = spec.polling
            self.board.add_subscription(spec.device,spec.attr,handler,polling)
        return self.board

### rule based pre and post conditions ###
## telescope starting up ##

def set_wating_for_start_up() -> MessageBoardBuilder:
    b = MessageBoardBuilder()
    # master devices
    # ignoring sdp master as it doesnt have polling set up
    b.set_waiting_on('mid_d0001/elt/master').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('mid_d0002/elt/master').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('mid_d0003/elt/master').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('mid_d0004/elt/master').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('mid_csp_cbf/sub_elt/master').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('mid_csp/elt/master').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('ska_mid/tm_central/central_node').for_attribute('State').to_become_equal_to('ON')
    # subarray devices
    b.set_waiting_on('ska_mid/tm_subarray_node/1').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('mid_csp_cbf/sub_elt/subarray_01').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('mid_csp/elt/subarray_01').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('ska_mid/tm_subarray_node/1').for_attribute('State').to_become_equal_to('ON')
    b.set_waiting_on('mid_sdp/elt/subarray_1').for_attribute('State').to_become_equal_to('ON')
    return b

## telescope shutting down
def set_wating_for_shut_down() -> MessageBoardBuilder:
    b = MessageBoardBuilder()
    # master devices
    # ignoring sdp master as it doesnt have polling set up
    b.set_waiting_on('mid_d0001/elt/master').for_attribute('State').to_become_equal_to('STANDBY')
    b.set_waiting_on('mid_d0002/elt/master').for_attribute('State').to_become_equal_to('STANDBY')
    b.set_waiting_on('mid_d0003/elt/master').for_attribute('State').to_become_equal_to('STANDBY')
    b.set_waiting_on('mid_d0004/elt/master').for_attribute('State').to_become_equal_to('STANDBY')
    b.set_waiting_on('mid_csp_cbf/sub_elt/master').for_attribute('State').to_become_equal_to('STANDBY')
    b.set_waiting_on('mid_csp/elt/master').for_attribute('State').to_become_equal_to('STANDBY')
    b.set_waiting_on('ska_mid/tm_central/central_node').for_attribute('State').to_become_equal_to('OFF')
    # subarray devices
    b.set_waiting_on('ska_mid/tm_subarray_node/1').for_attribute('State').to_become_equal_to('OFF')
    b.set_waiting_on('mid_csp_cbf/sub_elt/subarray_01').for_attribute('State').to_become_equal_to('OFF')
    b.set_waiting_on('mid_csp/elt/subarray_01').for_attribute('State').to_become_equal_to('OFF')
    b.set_waiting_on('ska_mid/tm_subarray_node/1').for_attribute('State').to_become_equal_to('OFF')
    b.set_waiting_on('mid_sdp/elt/subarray_1').for_attribute('State').to_become_equal_to('OFF')
    return b
    
## assigning resources

def set_waiting_for_assign_resources(id: int) -> MessageBoard:
    b = MessageBoardBuilder()
    b.set_waiting_on(f'ska_mid/tm_subarray_node/{id}').for_attribute('obsState').to_become_equal_to('ObsState.IDLE',master=True)
    b.set_waiting_on(f'mid_csp/elt/subarray_{id:02d}').for_attribute('obsState').and_observe()
    b.set_waiting_on(f'mid_sdp/elt/subarray_{id}').for_attribute('obsState').and_observe()
    for dishnr in range(1,3):
        #b.set_waiting_on(f'ska_mid/tm_leaf_node/d{dishnr:04d}').for_attribute('dishPointingState').and_observe()
        b.set_waiting_on(f'mid_d{dishnr:04d}/elt/master').for_attribute('pointingState').and_observe()
    return b

def set_waiting_for_release_resources(id: int) -> MessageBoard:
    b = MessageBoardBuilder()
    b.set_waiting_on(f'ska_mid/tm_subarray_node/{id}').for_attribute('obsState').to_become_equal_to('ObsState.EMPTY',master=True)
    b.set_waiting_on(f'mid_csp/elt/subarray_{id:02d}').for_attribute('obsState').and_observe()
    b.set_waiting_on(f'mid_sdp/elt/subarray_{id}').for_attribute('obsState').and_observe()
    for dishnr in range(1,3):
        #b.set_waiting_on(f'ska_mid/tm_leaf_node/d{dishnr:04d}').for_attribute('dishPointingState').and_observe()
        b.set_waiting_on(f'mid_d{dishnr:04d}/elt/master').for_attribute('pointingState').and_observe()
    return b

## configuring subarray

def set_waiting_for_configure_scan(id: int) -> MessageBoard:
    b = MessageBoardBuilder()
    subarray_change_order = [
        'ObsState.CONFIGURING',
        'ObsState.READY'
    ]
    b.set_waiting_on(f'ska_mid/tm_subarray_node/{id}').for_attribute('obsState').to_change_in_order(
        subarray_change_order,master=True)
    b.set_waiting_on(f'mid_csp/elt/subarray_{id:02d}').for_attribute('obsState').and_observe()
    b.set_waiting_on(f'mid_sdp/elt/subarray_{id}').for_attribute('obsState').and_observe()
    for dishnr in range(1,3):
        #b.set_waiting_on(f'ska_mid/tm_leaf_node/d{dishnr:04d}').for_attribute('dishPointingState').and_observe()
        b.set_waiting_on(f'mid_d{dishnr:04d}/elt/master').for_attribute('pointingState').and_observe()
    return b

def set_waiting_for_releasing_a_configuration(id: int) -> MessageBoard:
    b = MessageBoardBuilder()
    b.set_waiting_on(f'ska_mid/tm_subarray_node/{id}').for_attribute('obsState').to_become_equal_to('ObsState.IDLE',master=True)
    b.set_waiting_on(f'mid_csp/elt/subarray_{id:02d}').for_attribute('obsState').and_observe()
    b.set_waiting_on(f'mid_sdp/elt/subarray_{id}').for_attribute('obsState').and_observe()
    for dishnr in range(1,3):
        #b.set_waiting_on(f'ska_mid/tm_leaf_node/d{dishnr:04d}').for_attribute('dishPointingState').and_observe()
        b.set_waiting_on(f'mid_d{dishnr:04d}/elt/master').for_attribute('pointingState').and_observe()
    return b

## scanning
def set_waiting_for_scanning_to_complete(id: int) -> MessageBoard:

    b = MessageBoardBuilder()
    b.set_waiting_on(f'ska_mid/tm_subarray_node/{id}').for_attribute('obsState').to_change_in_order(['ObsState.SCANNING','ObsState.READY'],master=True)
    b.set_waiting_on(f'mid_csp/elt/subarray_{id:02d}').for_attribute('obsState').and_observe()
    b.set_waiting_on(f'mid_sdp/elt/subarray_{id}').for_attribute('obsState').and_observe()
    for dishnr in range(1,3):
        #b.set_waiting_on(f'ska_mid/tm_leaf_node/d{dishnr:04d}').for_attribute('dishPointingState').and_observe()
        b.set_waiting_on(f'mid_d{dishnr:04d}/elt/master').for_attribute('pointingState').and_observe()
    return b



## generic helpers for context managers and sync
def wait(board:MessageBoard, timeout: float, logger: Logger) -> None:
    for item in board.get_items(timeout):
        handler = item.handler
        handler.handle_event(item.event,item.subscription,logger)
        handler.print_event(item.event,ignore_first=True)
    return

### context managers and decorators for using rule based pre/post control
def print_logbook(board: MessageBoard,logger: logging.Logger)-> None:
    logbook = board.play_log_book()
    logger.info(f'Log Messages during waiting:\n{logbook}')


def print_when_exception(board: MessageBoard,logger: logging.Logger)-> None:
    logger.info('exception occured in execution of waiting')
    print_logbook(board,logger)
    logger.info(board.replay_self())
    #logger.info('subscription logs:')
    #logger.info(board.replay_subscriptions()) 


# telescope starting up
@contextmanager
def sync_telescope_starting_up(logger,timeout=10,log_enabled=False):
    builder = set_wating_for_start_up()
    board = builder.setup_board()
    try:
        yield
    except Exception as e:
        board.log('Canceling waiting as there was an error in executing startup')
        board.remove_all_subcriptions()
        print_when_exception(board,logger)
        raise e
    try:
        wait(board,timeout,logger)
    except Exception as e:
        print_when_exception(board,logger)
        raise e 
    if log_enabled:
        print_logbook(board,logger)


# telescope shutting down
@contextmanager
def sync_telescope_shutting_down(logger,timeout=10,log_enabled=False):
    builder = set_wating_for_shut_down()
    board = builder.setup_board()
    try:
        yield
    except Exception as e:
        board.log('Canceling waiting as there was an error in executing shutdown')
        board.remove_all_subcriptions()
        print_when_exception(board,logger)
        raise e
    try:
        wait(board,timeout,logger)
    except Exception as e:
        print_when_exception(board,logger)
        raise e 
    if log_enabled:
        print_logbook(board,logger)

def try_getting_wait_result(board: MessageBoard, future: futures.Future,timeout: int,silent: bool = False) -> None:
    try:
        future.result(timeout)
    except futures.TimeoutError as e:
        board.log('Unable to complete waiting on events as the task took too long')
        board.remove_all_subcriptions()
        if silent:
            board.log(f'Exception acknowlegded: {e}')
        else:
            raise e
    except EventTimedOut as e:
        board.log('Unable to complete waiting as some attributes still need to change:')
        if silent:
            board.log(f'Exception acknowlegded: {e}')
        else:
            raise e

## assigning resources
# assigning
@contextmanager
def sync_subarray_assigning(id,logger,timeout=10,log_enabled=False):
    builder = set_waiting_for_assign_resources(id)
    board = builder.setup_board()
    executor = futures.ThreadPoolExecutor(max_workers=1)
    future_wait_result = executor.submit(wait,board,timeout,logger)
    try:
        board.log('Starting subarray assigning...')
        yield
    except Exception as e:
        board.log('Subarray assignment call resulted in errors,...getting results from waiting on its state')
        try_getting_wait_result(board,future_wait_result,timeout,silent=True)
        print_when_exception(board,logger)
        raise e
    try:
        board.log('Subarray assignment call returned successfully...getting results from waiting on its state')
        try_getting_wait_result(board,future_wait_result,timeout)
    except Exception as e:
        print_when_exception(board,logger)
        raise e
    if log_enabled:
        print_logbook(board,logger)


# releasing
@contextmanager
def sync_subarray_releasing(id: int,logger,timeout=10,log_enabled=False):
    builder = set_waiting_for_release_resources(id)
    board = builder.setup_board()
    executor = futures.ThreadPoolExecutor(max_workers=1)
    future_wait_result = executor.submit(wait,board,timeout,logger)
    try:
        board.log('Starting subarray releasing...')
        yield
    except Exception as e:
        board.log('Subarray release call resulted in errors,...getting results from waiting on its state')
        try_getting_wait_result(board,future_wait_result,timeout,silent=True)
        print_when_exception(board,logger)
        raise e
    try:
        board.log('Subarray release call returned successfully...getting results from waiting on its state')
        try_getting_wait_result(board,future_wait_result,timeout)
    except Exception as e:
        print_when_exception(board,logger)
        raise e
    if log_enabled:
        print_logbook(board,logger)

## configuring
# configure a scan
@contextmanager
def sync_subarray_configuring(id: int,logger: logging.Logger,timeout: int =10,log_enabled: bool =False):
    builder = set_waiting_for_configure_scan(id)
    board = builder.setup_board()
    executor = futures.ThreadPoolExecutor(max_workers=1)
    future_wait_result = executor.submit(wait,board,timeout,logger)
    try:
        board.log('Starting subarray configuring..')
        yield
    except Exception as e:
        board.log('Subarray configure call resulted in errors,...getting results from waiting on its state')
        try_getting_wait_result(board,future_wait_result,timeout,silent=True)
        print_when_exception(board,logger)
        raise e
    try:
        board.log('Subarray configure call returned successfully...getting results from waiting on its state')
        try_getting_wait_result(board,future_wait_result,timeout)
    except Exception as e:
        print_when_exception(board,logger)
        raise e
    if log_enabled:
        print_logbook(board,logger)

#sync tear down configuration of a scan
@contextmanager
def sync_release_configuration(id: int,logger: logging.Logger,timeout: int =10,log_enabled: bool =False):
    builder = set_waiting_for_releasing_a_configuration(id)
    board = builder.setup_board()
    executor = futures.ThreadPoolExecutor(max_workers=1)
    future_wait_result = executor.submit(wait,board,timeout,logger)
    try:
        board.log('Starting subarray tear down of configuring..')
        yield
    except Exception as e:
        board.log('Subarray configure tear down resulted in an error,...getting results from waiting on its state')
        try_getting_wait_result(board,future_wait_result,timeout,silent=True)
        print_when_exception(board,logger)
        raise e
    try:
        board.log('Subarray configure tear down returned successfully...getting results from waiting on its state')
        try_getting_wait_result(board,future_wait_result,timeout)
    except Exception as e:
        print_when_exception(board,logger)
        raise e
    if log_enabled:
        print_logbook(board,logger)

watchSpec = namedtuple('watchSpec',['device','attr'])
@contextmanager
def observe_states(specs:List[Tuple[str,str]],logger,timeout=10,log_enabled=True):
    b = MessageBoardBuilder()
    for spec in  specs:
        b.set_waiting_on(spec.device).for_attribute(spec.attr,polling=False).and_observe()
    board = b.setup_board()
    try:
        yield
    finally:
        wait(board,timeout,logger)
        if log_enabled:
            print_logbook(board,logger)



  

   



        
        


    
