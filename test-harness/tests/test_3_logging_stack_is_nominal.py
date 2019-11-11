import pytest
import requests
import json

#TODO parametise and get this from k8s config somehow
INGRESS_HOSTNAME="kibana-logging-sarao"

def test_kibana_should_be_accessible_via_ingress():
    url = "http://{}:5601/app/kibana".format(INGRESS_HOSTNAME)
    res = requests.get(url)

    assert res.status_code == 200

