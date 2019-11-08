import pytest
import requests
import json

from pyhelm import ChartBuilder

#TODO parametise and get this from k8s config somehow
INGRESS_HOSTNAME="kibana-logging-sarao"

def test_kibana_should_be_accessible_via_ingress():
    url = f"http://{INGRESS_HOSTNAME}/app/kibana"
    res = requests.get(url)

    assert res.status_code == 200

