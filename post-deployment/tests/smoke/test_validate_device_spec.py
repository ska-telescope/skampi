import os
import socket
import pytest

from tango import DeviceProxy
from tango_simlib.utilities.validate_device import validate_device_from_url


# taken from https://github.com/tango-controls/pytango/blob/df925b55/tests/test_event.py#L30
@pytest.fixture(scope="class")
def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

class TestValidateDeviceInterface:
    """Tests for which verify that devices in deployed in skampi conform
    to their respective spec defined in the telescope model
    """

    def get_fqdn(self, port, device_name):
        tango_host = os.environ.get("TANGO_HOST", "")
        form = "tango://{0}:{1}/{2}"
        return form.format(tango_host, port, device_name)

    @pytest.mark.fast
    def test_dish_master_device_conforms_to_spec(self, get_open_port):
        port = get_open_port
        device_name = "mid_d0001/elt/master"
        fqdn = self.get_fqdn(port, device_name)
        url = "https://gitlab.com/ska-telescope/telescope-model/-/raw/user/johan/SAR-115/Add_YAML_device_spec/tango_device_specifications/ska_wide/ska_tango_guide_ska_wide.yaml"
        response = validate_device_from_url(fqdn, url, False)
        assert len(response) == 0, response
