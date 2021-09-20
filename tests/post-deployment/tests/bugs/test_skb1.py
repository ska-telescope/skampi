# When the MVP is deployed using Kubernetes ingress controller implemented by Traefik,
# TLS certificates are not served correctly. This results in https and secure
# websockets not being enabled. This test case is to verify this bug.
# To test using local ip address, assign local ip to env variable 'IP_FOR_INGRESS_TEST'
# and then run make k8s_test

import pytest
import socket
import os
import requests

@pytest.mark.skip
@pytest.mark.common
def test_check_connection():
    if os.getenv("IP_FOR_INGRESS_TEST") == None:
        host_ip = "192.168.93.47"  # IP of cluster master
    else:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)  # IP of this host
    ingress_host="k8s.stfc.skao.int"   # Ingress HTTP hostname
    url = "https://" + str(host_ip)
    exception = ""
    result = ""
    try:
        result = requests.get(url, headers={'host': ingress_host}, verify=True)
    except Exception as ex:
        exception = ex
    assert (exception == "" and "Response [200]" in str(result))
