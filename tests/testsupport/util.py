import logging
import socket
from datetime import datetime
from io import StringIO
from time import sleep

import yaml


def check_connection(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex((host, port))
    s.close()
    return result == 0


def wait_until(test_cmd, backoff_rate=1.5, retry_timeout=60):
    assert callable(test_cmd)
    test_cmd_name = getattr(test_cmd, '__name__', 'unknown')
    retry_start = datetime.now()
    retry_delay = 1
    try_count = 0
    while True:
        try_count += 1
        logging.debug("+++ Testing: {} x {}".format(test_cmd_name, str(try_count)))
        if test_cmd():
            break
        if int((datetime.now() - retry_start).total_seconds()) >= retry_timeout:
            raise TimeoutError(test_cmd)

        retry_delay *= backoff_rate
        logging.debug("+++ Retrying: {}, delay: {}".format(test_cmd_name, str(retry_delay)))
        sleep(retry_delay)


def parse_yaml_str(yaml_str):
    return [t for t in yaml.safe_load_all(StringIO(yaml_str)) if t is not None]
