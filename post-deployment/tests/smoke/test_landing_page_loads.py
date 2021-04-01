import requests
import pytest
import os
from assertpy import assert_that

@pytest.fixture(name='url')
def fxt_url():
    namespace = os.environ.get('KUBE_NAMESPACE','integration')
    host = os.environ.get('INGRESS_HOST',default='kubernetes.engageska-portugal.pt')
    return f'http://{host}/{namespace}/start/'

@pytest.mark.fast
@pytest.mark.skamid
@pytest.mark.skalow
def test_landing_page_loads(url):
    assert_that(requests.get(url).status_code).is_equal_to(200)