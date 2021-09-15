from tango import DeviceProxy,AttributeProxy
from time import sleep
import logging

class ArchiverHelper:

    def __init__(self,conf_manager='archiving/hdbpp/confmanager01', eventsubscriber='archiving/hdbpp/eventsubscriber01'):
        self.conf_manager = conf_manager
        self.eventsubscriber = eventsubscriber
        self.conf_manager_proxy = DeviceProxy(self.conf_manager)
        self.evt_subscriber_proxy = DeviceProxy(self.eventsubscriber)

    def attribute_add(self, fqdn, polling_period=1000, period_event=3000):
        if not self.is_already_archived(fqdn):
            AttributeProxy(fqdn).read()
            self.conf_manager_proxy.write_attribute("SetAttributeName", fqdn)
            self.conf_manager_proxy.write_attribute("SetArchiver", self.eventsubscriber)
            self.conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")
            self.conf_manager_proxy.write_attribute("SetPollingPeriod", int(polling_period))
            self.conf_manager_proxy.write_attribute("SetPeriodEvent", int(period_event))
            self.conf_manager_proxy.AttributeAdd()
            return True
        return False

    def attribute_list(self):
        return self.evt_subscriber_proxy.read_attribute("AttributeList").value

    def is_already_archived(self, fqdn):
        attr_list = self.attribute_list()
        if attr_list is not None:
            for already_archived in attr_list:
                if fqdn in str(already_archived).lower():
                    return True
        return False

    def start_archiving(self, fqdn=None, polling_period=1000, period_event=3000):
        if(fqdn is not None):
            self.attribute_add(fqdn,polling_period,period_event)
        return self.evt_subscriber_proxy.Start()

    def stop_archiving(self, fqdn):
        self.evt_subscriber_proxy.AttributeStop(fqdn)
        return self.conf_manager_proxy.AttributeRemove(fqdn)

    def evt_subscriber_attribute_status(self, fqdn):
        return self.evt_subscriber_proxy.AttributeStatus(fqdn)

    def conf_manager_attribute_status(self, fqdn):
        return self.conf_manager_proxy.AttributeStatus(fqdn)

    def is_started(self, fqdn):
        return "Archiving          : Started" in self.evt_subscriber_attribute_status(fqdn)

    def wait_for_start(self,fqdn,sleep_time=0.1,max_retries=30):
        total_sleep_time = 0
        for x in range(0, max_retries):
            try:
                if("Archiving          : Started" in self.conf_manager_attribute_status(fqdn)):
                    break
            except:
                pass
            sleep(sleep_time)
            total_sleep_time += 1
        return total_sleep_time* sleep_time
