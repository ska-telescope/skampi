from resources.test_support.waiting import Listener, StrategyListenbyPolling, StrategyListenbyPushing
from tango import DeviceProxy,EventType

def run_polling():
    p = DeviceProxy('test/device/1') 
    strategy1 = StrategyListenbyPolling(p) 
    l = Listener(p, strategy1,serverside_polling=True)
    p.pushscalarchangeevents('{"attribute_name": "double_scalar", "number_of_events": 10, "rate_of_events": 1}') 
    for event in l.get_events_on('long_scalar'):
        print(f'Event recieved on {event.get_date().strftime("%H:%M:%S")}:\nName: {event.attr_value.name}\nValue: {event.attr_value.value}')

def subscribe_basic(p, attr):
    return p.subscribe_event(attr,EventType.CHANGE_EVENT,10)

def get_events(p, sub_id):
    return p.get_events(sub_id)

def main():
    run_polling()

if __name__ == "__main__":
    main()
