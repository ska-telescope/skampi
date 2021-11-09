import os
import logging
import requests


def test_taranta():
    namespace = os.getenv("KUBE_NAMESPACE")
    host = os.getenv("INGRESS_HOST")
    url = f"http://{host}/{namespace}/taranta"
    logging.info(f"checking results from running a get on {url}")
    result = requests.get(url)
    logging.info(f"Result:\n{result}")
