from tango import DeviceProxy

class ArchiverHelper:

    def __init__(self,conf_manager='archiving/hdbpp/confmanager01', eventsubscriber='archiving/hdbpp/eventsubscriber01'):
        self.conf_manager = conf_manager
        self.eventsubscriber = eventsubscriber
        self.conf_manager_proxy = DeviceProxy(self.conf_manager)
        self.evt_subscriber_proxy = DeviceProxy(self.eventsubscriber)

    def attribute_add(self, fqdn, polling_period=1000, period_event=3000):
        self.conf_manager_proxy.write_attribute("SetAttributeName", fqdn)
        self.conf_manager_proxy.write_attribute("SetArchiver", self.eventsubscriber)
        self.conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")
        self.conf_manager_proxy.write_attribute("SetPollingPeriod", int(polling_period))
        self.conf_manager_proxy.write_attribute("SetPeriodEvent", int(period_event))
        return self.conf_manager_proxy.AttributeAdd()

    def attribute_list(self):
        return self.evt_subscriber_proxy.read_attribute("AttributeList").value

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
