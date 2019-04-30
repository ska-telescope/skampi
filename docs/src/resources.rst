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

K8s Commands
============
Get general information 

kubectl get all,pv,pvc,ingress -n integration

Describe a pod
Getting log from a container in pod


K8s Concepts
============
The following are key concepts to understand the project: 

* Pod: https://kubernetes.io/docs/concepts/workloads/pods/pod-overview/
* Service: https://kubernetes.io/docs/concepts/services-networking/service/
* StatefulSet: https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
* Ingress: https://kubernetes.io/docs/concepts/services-networking/ingress/
* IngressController: https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/
* Traefik IngressController: https://docs.traefik.io/user-guide/kubernetes/
* PersistentVolume: https://kubernetes.io/docs/concepts/storage/persistent-volumes/
* PersistentVolumeClaim: https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims

Readme File
===========

.. mdinclude:: ../../resources/README.md