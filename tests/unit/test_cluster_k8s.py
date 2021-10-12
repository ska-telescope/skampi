import os
import logging
import pytest
import time
import json
import requests
from pytest_bdd import scenario, given, when, then, scenarios, parsers
from kubernetes import client, config, watch
from kubernetes.stream import stream

@given(parsers.parse("a Kubernetes cluster with KUBECONFIG {kubeconfig}"))
def k8s_cluster(kubeconfig):
    logging.info("loading kubeconfig " + kubeconfig)
    config.load_kube_config(kubeconfig)

@when(parsers.parse("I create a pvc {name} with storage class {class_name}, accessModes {access_mode}, resources {resources}"))
def create_pvc(name, class_name, access_mode, resources, test_namespace):
    pvc_manifest = {
            'apiVersion': 'v1',
            'kind': 'PersistentVolumeClaim',
            'metadata': {
                'name': name
            },
            'spec':{
                'accessModes': [access_mode],
                'resources': {
                    'requests' : {
                        'storage' : resources
                    }
                },
                'storageClassName': class_name
            }
        }
    v1 = client.CoreV1Api()
    logging.info("Creating pvc " + name)
    v1.create_namespaced_persistent_volume_claim(test_namespace, pvc_manifest)
    if not hasattr(pytest, 'pvc'):
        pytest.pvc = []
    pytest.pvc.append(name)

@when(parsers.parse("I create a config map {name} from file {filename}"))
def create_configmap(name, filename,test_namespace):
    f = open(filename, 'r')
    file_value = f.read()
    configmap_manifest = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': name
            },
            'data': {
                os.path.basename(filename): file_value
            }
        }
    f.close()
    v1 = client.CoreV1Api()
    logging.info("Creating config map " + name)
    v1.create_namespaced_config_map(test_namespace, configmap_manifest)
    if not hasattr(pytest, 'config_maps'):
        pytest.config_maps = []
    pytest.config_maps.append(name)

@when(parsers.parse("I create a service {name} with image {image} (port {port}, replicas {replicas}) and volumes {vol0} (read-only {readonly}, mount path {path0}) and {vol1} (mount path {path1})"))
def create_service(name, image, port, replicas, vol0, readonly, path0, vol1, path1,test_namespace):
    service_manifest = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': name,
                'labels': {
                    'app': name
                }
            },
            'spec': {
                'selector': {
                    'app': name
                },
                'ports': [
                    {
                        'protocol': 'TCP',
                        'port': int(port),
                        'targetPort': int(port)
                    }
                ]
            }
        }
    deployment_manifest = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': name + '-deployment',
                'labels': {
                    'app': name
                }
            },
            'spec': {
                'replicas': int(replicas),
                'selector': {
                    'matchLabels': {
                        'app': name
                    }
                },
                'template': {
                    'metadata':{
                        'labels':{
                            'app': name
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': image,
                            'image': image,
                            'imagePullPolicy': 'IfNotPresent',
                            'ports': [{
                                'containerPort': int(port),
                                'protocol': 'TCP'
                            }],
                            'volumeMounts': [{
                                'mountPath': path0,
                                'name': vol0+ '-internal',
                                'readonly': readonly
                            },{
                                'mountPath': path1,
                                'name': vol1+ '-internal'
                            }]
                            }
                        ],
                        'volumes': [{
                            'name': vol0 + '-internal',
                            'persistentVolumeClaim':{
                                'claimName': vol0
                            }
                        },{
                            'name': vol1 + '-internal',
                            'configMap': {
                                'name': vol1
                            }
                        }]
                    }
                }
            }
        }
    v1 = client.CoreV1Api()
    appsv1 = client.AppsV1Api()
    logging.info("Creating service " + name)
    appsv1.create_namespaced_deployment(test_namespace, deployment_manifest)
    v1.create_namespaced_service(test_namespace, service_manifest)
    if not hasattr(pytest, 'services'):
        pytest.services = []
    pytest.services.append(name)
    if not hasattr(pytest, 'deployments'):
        pytest.deployments = []
    pytest.deployments.append(name + '-deployment')

@when(parsers.parse("I create an ingress {name} pointing to service {service_name}, service port {service_port}"))
def create_ingress(name, service_name, service_port,test_namespace):
    ingress_manifest = {
        'apiVersion': 'extensions/v1beta1',
        'kind': 'Ingress',
        'metadata':{
            'name': name,
            'labels': {
                'app.kubernetes.io/name': name
            }
        },
        'spec':{
            'rules': [{
                'host': service_name,
                'http': {
                    'paths': [{
                        'path': '/',
                        'backend': {
                            'serviceName': service_name,
                            'servicePort': int(service_port)
                        }
                    }]
                }
            }]
        }
    }
    beta = client.ExtensionsV1beta1Api()
    logging.info("Creating ingress " + name)
    beta.create_namespaced_ingress(test_namespace, ingress_manifest)
    if not hasattr(pytest, 'ingress'):
        pytest.ingress = []
    pytest.ingress.append(name)

@when(parsers.parse("the service {service_name} is ready"))
def verify_svc_ready(test_namespace, service_name):
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(test_namespace, label_selector='app=' + service_name)
    logging.info("Checking Pod Readiness...")
    while True:
        all_running = True
        for item in ret.items:
            if not item.status.phase == 'Running':
                all_running = False
                continue

            for status_container in item.status.container_statuses:
                if not status_container.ready:
                    all_running = False
                    break

        if(all_running):
            break
        else:
            ret = v1.list_namespaced_pod(test_namespace, label_selector='app=' + service_name)
    logging.info("Pod Ready")

@when(parsers.parse("I execute the command {command} on service {service_name}"))
def exec(command, service_name,test_namespace):
    exec_command = ['/bin/sh','-c', command]
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(test_namespace, label_selector='app=' + service_name)
    logging.info("Executing command " + command + " on pod " + ret.items[0].metadata.name)
    resp = stream(v1.connect_get_namespaced_pod_exec,
                  ret.items[0].metadata.name,
                  test_namespace,
                  command=exec_command,
                  stderr=True, stdin=False,
                  stdout=True, tty=False)
    # resp = v1.connect_get_namespaced_pod_exec( ret.items[0].metadata.name, test_namespace, command=exec_command, stderr=True, stdin=False, stdout=True, tty=False)
    logging.info(resp)

@then(parsers.parse("I can curl with hostname {host0}"))
def check_res(host0,test_namespace):
    try:
        logging.info("Checking results...")
        # Workaround from: https://github.com/kubernetes-client/python/issues/1284
        host_from_kubeconfig = client.Configuration().get_default_copy().host
        ip = host_from_kubeconfig.split("//")[1].split(':')[0]
        url = 'http://' + ip + "/"
        logging.info("URL1: {}".format(url))
        time.sleep(3)
        result1 = requests.get(url, headers={'Host': host0})
        logging.info("Result1: {}".format(result1.text))
        logging.info("Status1: {}".format(result1.status_code))
        assert result1.status_code == 200
    finally:
        v1 = client.CoreV1Api()
        beta = client.ExtensionsV1beta1Api()
        appsv1 = client.AppsV1Api()
        for pvc in pytest.pvc:
            logging.info("deleting pvc " + pvc)
            v1.delete_namespaced_persistent_volume_claim(pvc, test_namespace)
        for config_maps in pytest.config_maps:
            logging.info("deleting config map " + config_maps)
            v1.delete_namespaced_config_map(config_maps, test_namespace)
        for service in pytest.services:
            logging.info("deleting service " + service)
            v1.delete_namespaced_service(service, test_namespace)
        for deployment in pytest.deployments:
            logging.info("deleting deployment " + deployment)
            appsv1.delete_namespaced_deployment(deployment, test_namespace)
        for ing in pytest.ingress:
            logging.info("deleting ingress " + ing)
            beta.delete_namespaced_ingress(ing, test_namespace)

        pytest.pvc = []
        pytest.config_maps = []
        pytest.services = []
        pytest.deployments = []
        pytest.ingress = []


@then(parsers.parse("a curl with hostname {host0} and {host1} return the same result"))
def check_res(host0, host1,test_namespace):
    try:
        logging.info("Checking results...")
        # Workaround from: https://github.com/kubernetes-client/python/issues/1284
        host_from_kubeconfig = client.Configuration().get_default_copy().host
        ip = host_from_kubeconfig.split("//")[1].split(':')[0]
        url = 'http://' + ip + "/"
        logging.info("URL1: {}".format(url))
        time.sleep(3)
        result1 = requests.get(url, headers={'Host': host0})
        result2 = requests.get(url, headers={'Host': host1})
        logging.info("Result1: {}".format(result1.text))
        logging.info("Status1: {}".format(result1.status_code))
        logging.info("Result2: {}".format(result2.text))
        logging.info("Status2: {}".format(result2.status_code))
        assert result1.status_code == 200
        assert result2.status_code == 200
        assert result1.text == result2.text
    finally:
        v1 = client.CoreV1Api()
        beta = client.ExtensionsV1beta1Api()
        appsv1 = client.AppsV1Api()
        for pvc in pytest.pvc:
            logging.info("deleting pvc " + pvc)
            v1.delete_namespaced_persistent_volume_claim(pvc, test_namespace)
        for config_maps in pytest.config_maps:
            logging.info("deleting config map " + config_maps)
            v1.delete_namespaced_config_map(config_maps, test_namespace)
        for service in pytest.services:
            logging.info("deleting service " + service)
            v1.delete_namespaced_service(service, test_namespace)
        for deployment in pytest.deployments:
            logging.info("deleting deployment " + deployment)
            appsv1.delete_namespaced_deployment(deployment, test_namespace)
        for ing in pytest.ingress:
            logging.info("deleting ingress " + ing)
            beta.delete_namespaced_ingress(ing, test_namespace)
        pytest.pvc = []
        pytest.config_maps = []
        pytest.services = []
        pytest.deployments = []
        pytest.ingress = []

scenarios('../features/cluster_k8s.feature')
