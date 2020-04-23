# When the MVP is deployed using Kubernetes ingress controller implemented by Traefik,
# TLS certificates are not served correctly. This results in https and secure
# websockets not being enabled. This test case is to verify this bug.

import subprocess
import pytest
import socket
import os

os.environ["USE_LOCAL_HOST_IP_FOR_SSL_TEST"] = "True"


@pytest.mark.xfail
def test_check_connection():
    if os.environ["USE_LOCAL_HOST_IP_FOR_SSL_TEST"] == "True":
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)    # IP of this host
    else:
        host_ip="192.168.93.47"

    ingress_host="integration.engageska-portugal.pt"   # Ingress HTTP hostname

    test_ssl="curl -v https://" + str(host_ip) + " -H 'Host: " + ingress_host + " '2>&1 | awk 'BEGIN " \
                                    "{ cert=0 } /^\* SSL connection/ { cert=1 } /^\*/ { if (cert) print }'"
    res = subprocess.run(test_ssl, shell=True, universal_newlines=True, stderr=subprocess.PIPE)
    assert ("error" not in res.stderr and "Closing connection 0" not in res.stderr)
