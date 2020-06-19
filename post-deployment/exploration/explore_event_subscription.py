from resources.test_support.waiting import Listener, StrategyListenbyPolling, StrategyListenbyPushing
from tango import DeviceProxy,EventType

def run_polling():
    p = DeviceProxy('test/device/1') 
    strategy1 = StrategyListenbyPolling(p) 
    l = Listener(p, strategy1)
    p.pushscalarchangeevents('{"attribute_name": "double_scalar", "number_of_events": 10, "rate_of_events": 1}') 
    event_counter = 0
    for event in l.get_events_on('double_scalar'):
        print(f'Event nr {event_counter} recieved on {event.get_date().strftime("%H:%M:%S")}:\nName: {event.attr_value.name}\nValue: {event.attr_value.value}')
        if event_counter == 9:
            l.stop_listening()
        event_counter +=1

def run_pushing_periodically():
    p = DeviceProxy('test/device/1') 
    strategy = StrategyListenbyPushing(p) 
    l = Listener(p, strategy, serverside_polling=False)
    p.pushscalarchangeevents('{"attribute_name": "double_scalar", "number_of_events": 10, "rate_of_events": 1}') 
    event_counter = 0
    for event in l.get_events_on('double_scalar'):
        print(f'Event nr {event_counter} recieved on {event.get_date().strftime("%H:%M:%S")}:\nName: {event.attr_value.name}\nValue: {event.attr_value.value}')
        if event_counter == 9:
            l.stop_listening()
        event_counter +=1

def run_pushing():
    p = DeviceProxy('test/device/1') 
    strategy1 = StrategyListenbyPushing(p) 
    l = Listener(p, strategy1)
    p.pushscalarchangeevents('{"attribute_name": "double_scalar", "number_of_events": 10, "rate_of_events": 1}') 
    event_counter = 0
    for event in l.get_events_on('double_scalar'):
        print(f'Event nr {event_counter} recieved on {event.get_date().strftime("%H:%M:%S")}:\nName: {event.attr_value.name}\nValue: {event.attr_value.value}')
        if event_counter == 9:
            l.stop_listening()
        event_counter +=1


def main():
    run_polling()

if __name__ == "__main__":
    main()
