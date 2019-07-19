TM integration
==============

K8s Concepts
------------
The following are key concepts to understand the project: 

* Namespace: https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/#when-to-use-multiple-namespaces
* Pod: https://kubernetes.io/docs/concepts/workloads/pods/pod-overview/
* Service: https://kubernetes.io/docs/concepts/services-networking/service/
* StatefulSet: https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
* Ingress: https://kubernetes.io/docs/concepts/services-networking/ingress/
* IngressController: https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/
* Traefik IngressController: https://docs.traefik.io/user-guide/kubernetes/
* PersistentVolume: https://kubernetes.io/docs/concepts/storage/persistent-volumes/
* PersistentVolumeClaim: https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims

KubeCtl references
------------------
Overview: https://kubernetes.io/docs/reference/kubectl/overview/
Cheat Sheet: https://kubernetes.io/docs/reference/kubectl/cheatsheet/

K8s Templates
-------------

Template files follow the standard conventions for writing Go templates (see the `documentation <https://golang.org/pkg/text/template/>`_ for details). 
For example, in the tango-base chart, the following files composes the templates for the generation of valid kubernetes manifest files: 

* tangodb.yaml: define a k8s service for maria db and a statefulset attached to it
* tangodb-pv.yaml: define a PersistentVolume and a PersistentVolumeClaim for the database service (tangodb.yaml)
* databaseds.yaml: define a k8s service for the device server Databaseds and a statefulset attached to it
* itango.yaml: define a k8s pod for interacting with other containers (for local testing purpose)
* jive.yaml: define a k8s pod for interacting with the tango jive tool (for local development purpose)
* logviewer.yaml: define a k8s pod for interacting with the tango logviewer tool  (for local development purpose)
* tangotest.yaml: define a k8s pod for the tangotest device server

K8s Tags
--------
Below there are the main tags that constitute every object in the k8s integration. 

Metadata tag
^^^^^^^^^^^^
Every yaml file has a metadata tag which specify some important information like:

* name: a string that uniquely identifies this object within the current namespace (see the identifiers docs). This value is used in the path when retrieving an individual object.
* namespace: a namespace is a DNS compatible label that objects are subdivided into.
* `labels <https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/>`_: a map of string keys and values that can be used to organize and categorize objects
    * app: unique name (equals to name above) 
    * chart: name of the chart
    * release and heritage: used by helm for install/upgrade

Spec
^^^^
Every yaml file has a spec tag which is used to set all the parameters for a specific object. For instance, in `databaseds.yaml <https://github.com/ska-telescope/k8s-integration/blob/master/chart/templates/databaseds.yaml>`_ the StatefulSet object specifies that the label 'app' should match with a specific value and that the related service is the one specified in the tag 'serviceName'. 

.. code-block:: console

  selector:
    matchLabels:
      app: databaseds-{{ template "tango-base.name" . }}-{{ .Release.Name }}
  serviceName: databaseds-{{ template "tango-base.name" . }}-{{ .Release.Name }}

initContainers
^^^^^^^^^^^^^^
A Pod can have multiple Containers running apps within it, but it can also have one or more Init Containers, which are run before the app Containers are started. Check `documentation <https://kubernetes.io/docs/concepts/workloads/pods/init-containers/>`_ for more information.

containers
^^^^^^^^^^

The containers tag includes the containers that form the specific pod or object whithin k8s. 
