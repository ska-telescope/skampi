from resources.test_support.helpers import resource
from datetime import date,datetime
from time import time, sleep
import threading
import logging



class StateChecker():

    def __init__(self,resources,state_name='obsState',max_nr_of_records=None):
        self.resources = resources
        self.th_records = []
        self.state_name = state_name
        self.th_running = False
        self.lock = threading.Lock()
        self.max_nr_of_records = max_nr_of_records
        

    def _get_running(self):
        with self.lock:
            value = self.th_running
        return value

    def _set_running(self):
        with self.lock:
            self.th_running = True
        
    def _clear_running(self):
        with self.lock:
            self.th_running = False
 
    def _update_records(self,list):
        with self.lock:
            self.th_records = list

    def get_records(self,filtered=False):
        with self.lock:
            is_allowed = not self.th_running
        if is_allowed:
            if filtered:
                return [record for record in self.th_records if record['unique']]
            else:
                return self.th_records
        

    def run(self,threaded=True,resolution=0.1):
        self._set_running()
        max_nr_of_records = self.max_nr_of_records
        if not threaded:
            #need to have a deafult value for max nr of records other will run always
            if max_nr_of_records == None:
                max_nr_of_records = 100
            self._loop(self.resources,self.state_name,resolution,max_nr_of_records)
        else:
            self.thread = threading.Thread(target=self._loop, args=(self.resources,self.state_name,resolution,max_nr_of_records))
            self.thread.start()
    
    def stop(self):
        self._clear_running()
        self.thread.join()

    def _get_filter_states_from_record(self,record):
        keys = record.keys()
        return [record[key] for key in keys if " state" in key]


    def _is_unique(self,list,record):
        if list == []:
            return True
        previous_filtered_states = self._get_filter_states_from_record(list[-1])
        current_filteres_states = self._get_filter_states_from_record(record)
        if previous_filtered_states == current_filteres_states:
            return False
        else:
            return True


    def _loop(self,resources,state_name,resolution,max_nr_of_records):
        n = 0
        list = []
        while self._get_running():
            n +=1
            record = {}
            start_time = time()
            record['seq'] = n
            record['time_window'] = datetime.now().strftime('%H:%M:%S.%f')[:-3] 
            for resource_name in resources:
                record['{} state'.format(resource_name)] = resource(resource_name).get(state_name)
                record['{} delta'.format(resource_name)] = '{:f}'.format(time() - start_time)
            if self._is_unique(list,record):
                record['unique'] = True
            else:
                record['unique'] = False
            list.append(record)
            if max_nr_of_records != None:
                if n >= max_nr_of_records:
                    logging.debug('nr of records ({}) is above max {}, stopping'.format(n,max_nr_of_records))
                    self._clear_running()
                    break
            time_left_to_sleep = abs(resolution - (time() - start_time))
            sleep(time_left_to_sleep)  
        self._update_records(list)

