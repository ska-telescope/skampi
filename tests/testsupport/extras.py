import subprocess

import requests

from tests.testsupport.util import check_connection, wait_until, parse_yaml_str


class EchoServer(object):
    DEFINITION_FILE = 'tests/testsupport/extras/echoserver.yaml'
    LISTEN_PORT = 9001

    def __init__(self, namespace, local_port=LISTEN_PORT):
        with open(self.DEFINITION_FILE, 'r') as f:
            self.definition = parse_yaml_str(f.read())
        self.namespace = namespace
        self.local_port = local_port

        self._deploy()
        self._proxy()

    def _deploy(self, wait=True):
        subprocess.run("kubectl apply -n {} -f {}".format(self.namespace, self.DEFINITION_FILE).split(),
                       check=True)
        if wait:
            wait_until(self.is_running)

    def _proxy(self, wait=True):
        self._proxy_proc = subprocess.Popen(
            "kubectl port-forward -n {} pod/echoserver {}:{}".format(self.namespace, self.local_port, self.LISTEN_PORT).split())

        if wait:
            wait_until(self.is_proxied_locally)

    def print_to_stdout(self, line):
        requests.post("http://127.0.0.1:{}/echo".format(self.local_port), line)

    def delete(self):
        self._proxy_proc.kill()
        for resource in self.definition:
            subprocess.run(
                "kubectl delete {} {} -n {}".format(resource['kind'],
                                                    resource['metadata']['name'],
                                                    self.namespace).split(), check=True)

    def is_running(self):
        cmd = "kubectl describe pod echoserver -n {} | grep -q 'Status:.*Running'".format(
            self.namespace)
        return subprocess.run(cmd, shell=True).returncode == 0

    def is_proxied_locally(self):
        return check_connection('127.0.0.1', self.local_port)