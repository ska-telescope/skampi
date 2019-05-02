Available resources
===================

In the repository there is a folder called "resources" which is a collection of resources used for testing and for configuration. 

+-----------------------+-------------------------------------------------------+
| File                  | Description                                           |
+=======================+=======================================================+
| configuration.yaml    | First version of the configuration script used by the |
|                       | tmc-prototype to configure the database. It reads the |
|                       | file devices.json and configure the database          |
|                       | accordingly.                                          |
+-----------------------+-------------------------------------------------------+
| devices.json          | Used by the configuration.yaml script to configure    |
|                       | the database.                                         |
+-----------------------+-------------------------------------------------------+
| graphql.query.test    | It contains a graphql query to test the related       |
|                       | webjive service.                                      |
+-----------------------+-------------------------------------------------------+
| traefik-minikube.yaml | Definition of the traefik ingress controller          |
+-----------------------+-------------------------------------------------------+

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
| apply           | apply resource descriptor k8s.yml                                   |
+-----------------+---------------------------------------------------------------------+
| logs            | POD logs for descriptor                                             |
+-----------------+---------------------------------------------------------------------+
| rm              | delete applied resources                                            |
+-----------------+---------------------------------------------------------------------+
| namespace       | create the kubernetes namespace                                     |
+-----------------+---------------------------------------------------------------------+
| deploy          | deploy the helm chart                                               |
+-----------------+---------------------------------------------------------------------+
| show            | show the helm chart                                                 |
+-----------------+---------------------------------------------------------------------+
| delete          | delete the helm chart release                                       |
+-----------------+---------------------------------------------------------------------+
| poddescribe     | describe Pods executed from Helm chart                              |
+-----------------+---------------------------------------------------------------------+
| podlogs         | show Helm chart POD logs                                            |
+-----------------+---------------------------------------------------------------------+
| localip         | set local Minikube IP in /etc/hosts file for apigateway             |
+-----------------+---------------------------------------------------------------------+
| help            | Show the help summary                                               |
+-----------------+---------------------------------------------------------------------+


.. toctree::
   :maxdepth: 1
   :caption: Readme File:

   resources-readme
