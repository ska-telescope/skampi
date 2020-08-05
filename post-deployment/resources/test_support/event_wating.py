from resources.test_support.subscribing import EventData,MessageBoard,MessageHandler,Tuple,List
from collections import namedtuple
from logging import Logger
from contextlib import contextmanager
from tango import DevState, TimeVal
from typing import Callable, ClassVar,Tuple, Set
from functools import partial
from time import sleep

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

    def __init__(self,board, attr: str, value: str, device: str) -> None:
        self.attr = attr
        self.device = device
        self.desired_value = value
        self.events =[]
        super(WaitUntilEqual,self).__init__(board)

    def describe_self(self) -> str:
        return f'handler that waits for {self.attr} on device {self.device} to be equal to {self.desired_value}'

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


    def handle_event(self,event: EventData, subscription: object, logger) -> None:
        with self.handle_context(event,subscription):
            self.update(event)
            if self.condition_met():
                self.unsubscribe(subscription)
        
    def supress_timeout(self) -> bool:
        return False

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

def set_waiting_for_assign_resources():
    b = MessageBoardBuilder()
    b.set_waiting_on('ska_mid/tm_subarray_node/1').for_attribute('obsState').to_become_equal_to('ObsState.IDLE')
    return b

def set_waiting_for_release_resources():
    b = MessageBoardBuilder()
    b.set_waiting_on('ska_mid/tm_subarray_node/1').for_attribute('obsState').to_become_equal_to('ObsState.EMPTY')
    return b



## generic helpers for context managers and sync
def wait(board:MessageBoard, timeout: float, logger: Logger):
    print_message = 'incoming events'
    for item in board.get_items(timeout):
        handler = item.handler
        handler.handle_event(item.event,item.subscription,logger)
        print_message = f'{print_message}{handler.print_event(item.event,ignore_first=True)}'
    logger.debug(print_message)

### context managers and decorators for using rule based pre/post control


# telescope starting up
@contextmanager
def sync_telescope_starting_up(logger,timeout=10):
    builder = set_wating_for_start_up()
    board = builder.setup_board()
    yield
    try:
        wait(board,timeout,logger)
    except Exception as e:
        logger.info(board.replay_self())
        logger.info(board.replay_subscriptions()) 
        raise e 
    finally:
        pass



# telescope shutting down
@contextmanager
def sync_telescope_shutting_down(logger,timeout=10):
    builder = set_wating_for_shut_down()
    board = builder.setup_board()
    yield
    try:
        wait(board,timeout,logger)
    except Exception as e:
        logger.info(board.replay_self())
        logger.info(board.replay_subscriptions()) 
        raise e 
    finally:
        pass

## assigning resources
# assigning
@contextmanager
def sync_subarray1_assigning(logger,timeout=10):
    builder = set_waiting_for_assign_resources()
    board = builder.setup_board()
    yield
    try:
        wait(board,timeout,logger)
    except Exception as e:
        logger.info(board.replay_self())
        logger.info(board.replay_subscriptions())
        raise e 
    finally:
        pass  


# releasing
@contextmanager
def sync_subarray1_releasing(logger,timeout=10):
    builder = set_waiting_for_release_resources()
    board = builder.setup_board()
    yield
    try:
        wait(board,timeout,logger)
    except Exception as e:
        logger.info(board.replay_self())
        logger.info(board.replay_subscriptions()) 
        raise e 
    finally:
        pass

watchSpec = namedtuple('watchSpec',['device','attr'])
@contextmanager
def observe_states(specs:List[Tuple[str,str]],logger,timeout=10):
    b = MessageBoardBuilder()
    for spec in  specs:
        b.set_waiting_on(spec.device).for_attribute(spec.attr,polling=False).and_observe()
    board = b.setup_board()
    yield
    try:
        wait(board,timeout,logger)
    except Exception as e:
        logger.info(board.replay_self())
        logger.info(board.replay_subscriptions()) 
        raise e 
    finally:
        pass



  

   



        
        


    
