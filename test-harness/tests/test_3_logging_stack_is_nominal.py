import os
import pytest
import requests
import json
import pytest

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def requests_retry_session(retries=3,
        backoff_factor=0.3, 
        status_forcelist=(500, 502, 504),
        session=None):

    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def test_kibana_should_be_accessible_via_ingress(run_context):
    HOSTNAME = "kibana-logging-{}".format(run_context.HELM_RELEASE)
    BASE_PATH = "/kibana"

    url = "http://{}:5601{}/app/kibana".format(HOSTNAME, BASE_PATH)
    res = requests_retry_session().get(url)

    assert res.status_code == 200

