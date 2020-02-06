Available resources
===================

The folder called "resources" is a collection of resources used for testing and for configuration. 

Makefile targets
----------------
This project contains a Makefile which defines the following targets:

+-----------------+---------------------------------------------------------------------+
| Makefile target | Description                                                         |
+=================+=====================================================================+
| vars            | Display variables - pass in DISPLAY and XAUTHORITY                  |
+-----------------+---------------------------------------------------------------------+
| k8s             | Which kubernetes are we connected to                                |
+-----------------+---------------------------------------------------------------------+
| k8s_test        | test the application on K8s                                         |
+-----------------+---------------------------------------------------------------------+
| apply           | apply resource descriptor k8s.yml                                   |
+-----------------+---------------------------------------------------------------------+
| get_versions    | lists the container images used for particular pods                 |
+-----------------+---------------------------------------------------------------------+
| logs            | POD logs for descriptor                                             |
+-----------------+---------------------------------------------------------------------+
| rm              | delete applied resources                                            |
+-----------------+---------------------------------------------------------------------+
| namespace       | create the kubernetes namespace                                     |
+-----------------+---------------------------------------------------------------------+
| deploy_all      | deploy ALL of the helm chart                                        |
+-----------------+---------------------------------------------------------------------+
| deploy_etcd     | deploy etcd-operator into namespace                                 |
+-----------------+---------------------------------------------------------------------+
| deploy          | deploy the helm chart                                               |
+-----------------+---------------------------------------------------------------------+
| show            | show the helm chart                                                 |
+-----------------+---------------------------------------------------------------------+
| delete_all      | delete ALL of the helm chart release                                |
+-----------------+---------------------------------------------------------------------+
| delete_etcd     | Remove etcd-operator from namespace                                 |
+-----------------+---------------------------------------------------------------------+
| delete          | delete the helm chart release                                       |
+-----------------+---------------------------------------------------------------------+
| traefik         | install the helm chart for traefik (in the kube-system namespace)   |
+-----------------+---------------------------------------------------------------------+
| delete_traefik  | delete the helm chart for traefik                                   |
+-----------------+---------------------------------------------------------------------+
| gangway         | install gangway authentication for gitlab (kube-system namespace)   |
+-----------------+---------------------------------------------------------------------+
| delete_gangway  | delete gangway authentication for gitlab                            |
+-----------------+---------------------------------------------------------------------+
| poddescribe     | describe Pods executed from Helm chart                              |
+-----------------+---------------------------------------------------------------------+
| podlogs         | show Helm chart POD logs                                            |
+-----------------+---------------------------------------------------------------------+
| localip         | set local Minikube IP in /etc/hosts file for apigateway             |
+-----------------+---------------------------------------------------------------------+
| help            | Show the help summary                                               |
+-----------------+---------------------------------------------------------------------+


Ansible
-------

It is possible to setup a local SKAMPI environment using the ansible playbook available `here <https://github.com/ska-telescope/ansible-playbooks#skampi>`_.


.. toctree::
   :maxdepth: 1
   :caption: Readme File:

   resources-readme
   resources-auth-readme
