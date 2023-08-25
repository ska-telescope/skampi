from time import sleep

from tango import AttributeProxy, ConnectionFailed, DeviceProxy


class ArchiverHelper:
    def __init__(self, conf_manager, eventsubscriber):
        self.conf_manager = conf_manager
        self.eventsubscriber = eventsubscriber
        self.conf_manager_proxy = get_proxy(self.conf_manager)
        self.evt_subscriber_proxy = get_proxy(self.eventsubscriber)

    def attribute_add(self, fqdn, strategy, polling_period, value):
        """
        Adds the specified attribute to the archive configuration.

        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :param polling_period: Polling period in milliseconds.
        :type polling_period: int
        :param strategy: strategy for archiving.
        :type strategy: str
        :param value: value for  strategy specified.
        :type value: Union[ int , bool]
        :return: True or False
        """
        if not self.is_already_archived(fqdn):
            AttributeProxy(fqdn).read()
            self.conf_manager_proxy.write_attribute("SetAttributeName", fqdn)
            self.conf_manager_proxy.write_attribute("SetArchiver", self.eventsubscriber)
            self.conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")
            self.conf_manager_proxy.write_attribute(strategy, value)
            if polling_period:
                self.conf_manager_proxy.write_attribute("SetPollingPeriod", int(polling_period))
            self.conf_manager_proxy.AttributeAdd()
            return True
        return False

    def attribute_list(self):
        """
        Method for attribute list

        :return: Attribute list
        """

        return self.evt_subscriber_proxy.AttributeList

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

    def start_archiving(self, fqdn=None, strategy=None, polling_period=1000, value=None):
        """
        A method for initializing archiving process
        :param fqdn: Fully qualified domain name of the attribute to be added.
        :type fqdn: str
        :param polling_period: Polling period in milliseconds. Default is 1000.
        :type polling_period: int
        :param strategy: strategy for archiving.
        :type strategy: str
        :param value: value for given strategy.
        :type value : Union[ int, bool]
        :return: Start on archiver

        """
        if fqdn is not None:
            self.attribute_add(fqdn, strategy, polling_period, value)
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
        return "Archiving          : Started" in self.evt_subscriber_attribute_status(fqdn)

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
        for _ in range(0, max_retries):
            try:
                if "Archiving          : Started" in self.conf_manager_attribute_status(fqdn):
                    break
            except Exception:
                pass
            sleep(sleep_time)
            total_sleep_time += 1
        return total_sleep_time * sleep_time


def get_proxy(device_name: str, retries: int = 3):
    """Method retries if connection failed during proxy creation
    :param device_name: device name
    :type device_name: str
    :param retries: no of retries to create proxy
    : type retries: int
    :return: device proxy
    :raises ConnectionFailed: raises connection failed exception.

    """
    retry = 0
    no_of_retries = retries
    while retry <= no_of_retries:
        try:
            return DeviceProxy(device_name)
        except ConnectionFailed as connection_failed:
            retry += 1
            if retry == 4:
                raise connection_failed
            sleep(10)
