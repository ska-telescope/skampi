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

    def get_records(self):
        with self.lock:
            is_allowed = not self.th_running
        if is_allowed:
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

    def _loop(self,resources,state_name,resolution,max_nr_of_records):
        n = 0
        list = []
        while self._get_running():
            n +=1
            record = {}
            start_time = time()
            record['seq'] = n
            record['time_window'] = datetime.now().strftime('%H:%M:%S')
            for resource_name in resources:
                record['{} state'.format(resource_name)] = resource(resource_name).get(state_name)
                record['{} delta'.format(resource_name)] = '{:f}'.format(time() - start_time)
            list.append(record)
            if max_nr_of_records != None:
                if n >= max_nr_of_records:
                    logging.debug('nr of records ({}) is above max {}, stopping'.format(n,max_nr_of_records))
                    self._clear_running()
                    break
            sleep(resolution)  
        self._update_records(list)

