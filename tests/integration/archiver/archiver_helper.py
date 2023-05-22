from time import sleep

from tango import AttributeProxy, DeviceProxy


class ArchiverHelper:
    def __init__(
        self, conf_manager="mid-eda/cm/01", eventsubscriber="mid-eda/es/01"
    ):
        self.conf_manager = conf_manager
        self.eventsubscriber = eventsubscriber
        self.conf_manager_proxy = DeviceProxy(self.conf_manager)
        self.evt_subscriber_proxy = DeviceProxy(self.eventsubscriber)

    def attribute_add(self, fqdn, polling_period=1000, period_event=3000):
        """
        Adds the specified attribute to the archive configuration.

        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :param polling_period: Polling period in milliseconds. Default is 1000.
        :type polling_period: int
        :param period_event: Period event in milliseconds. Default is 3000.
        :type period_event: int
        :return: True or False
        """
        if not self.is_already_archived(fqdn):
            AttributeProxy(fqdn).read()
            self.conf_manager_proxy.write_attribute("SetAttributeName", fqdn)
            self.conf_manager_proxy.write_attribute(
                "SetArchiver", self.eventsubscriber
            )
            self.conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")
            self.conf_manager_proxy.write_attribute(
                "SetPollingPeriod", int(polling_period)
            )
            self.conf_manager_proxy.write_attribute(
                "SetPeriodEvent", int(period_event)
            )
            self.conf_manager_proxy.AttributeAdd()
            return True
        return False

    def attribute_list(self):
        """
        Method for attribute list

        :return: Attribute list
        """
        return self.evt_subscriber_proxy.read_attribute("AttributeList").value

    def is_already_archived(self, fqdn):
        """
        Object to check if attribute is already archived
        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: True if attribute is already archived
        """
        attr_list = self.attribute_list()
        if attr_list is not None:
            for already_archived in attr_list:
                if fqdn in str(already_archived).lower():
                    return True
        return False

    def start_archiving(
        self, fqdn=None, polling_period=1000, period_event=3000
    ):
        """
        A method for initializing archiving process
        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :param polling_period: Polling period in milliseconds. Default is 1000.
        :type polling_period: int
        :param period_event: Period event in milliseconds. Default is 3000.
        :type period_event: int
        :return: Start on archiver

        """
        if fqdn is not None:
            self.attribute_add(fqdn, polling_period, period_event)
        return self.evt_subscriber_proxy.Start()

    def stop_archiving(self, fqdn):
        """
        A method for stopping archiving process
        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: removed attribute
        """
        self.evt_subscriber_proxy.AttributeStop(fqdn)
        return self.conf_manager_proxy.AttributeRemove(fqdn)

    def evt_subscriber_attribute_status(self, fqdn):
        """
        A method to get event subscriber attribute status
        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: event subscriber attribute status
        """
        return self.evt_subscriber_proxy.AttributeStatus(fqdn)

    def conf_manager_attribute_status(self, fqdn):
        """
        A method to get configuration manager attribute status
        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: configuration manager attribute status
        """
        return self.conf_manager_proxy.AttributeStatus(fqdn)

    def is_started(self, fqdn):
        """
        A method to know if archiving is started
        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :return: status
        """
        return (
            "Archiving          : Started"
            in self.evt_subscriber_attribute_status(fqdn)
        )

    def wait_for_start(self, fqdn, sleep_time=0.1, max_retries=30):
        """
        A method to wait for starting archiver
        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :param sleep_time: Default is 0.1
        :param max_retries: Default is 30
        :return: total sleep time
        """
        total_sleep_time = 0
        while max_retries > 0:
            max_retries -= 1
            try:
                if (
                    "Archiving          : Started"
                    in self.conf_manager_attribute_status(fqdn)
                ):
                    break
            except Exception:
                pass
            sleep(sleep_time)
            total_sleep_time += 1
        return total_sleep_time * sleep_time
