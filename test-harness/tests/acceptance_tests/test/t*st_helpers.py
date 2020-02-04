import pytest

from helpers import resource

class TestResource(object):
    def test_init(self):
        """
        Test the __init__ method.
        """
        name = 'name'
        r = resource(name)
        assert r.device_name == name
