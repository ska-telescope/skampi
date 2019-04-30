Helm templates
====================

K8s Concepts
------------
The following are key concepts to understand the project: 

* Pod: https://kubernetes.io/docs/concepts/workloads/pods/pod-overview/
* Service: https://kubernetes.io/docs/concepts/services-networking/service/
* StatefulSet: https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
* Ingress: https://kubernetes.io/docs/concepts/services-networking/ingress/
* IngressController: https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/
* Traefik IngressController: https://docs.traefik.io/user-guide/kubernetes/
* PersistentVolume: https://kubernetes.io/docs/concepts/storage/persistent-volumes/
* PersistentVolumeClaim: https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims


Templates
---------

The following files composes the templates for the generation of valid kubernetes manifest files: 

* tangodb.yaml: define a k8s service for maria db and a statefulset attached to it
* databaseds.yaml: define a k8s service for the device server Databaseds and a statefulset attached to it
* itango.yaml: define a k8s pod for interacting with other containers (for local testing purpose)
* jive.yaml: define a k8s pod for interacting with the tango jive tool (for local development purpose)
* logviewer.yaml: define a k8s pod for interacting with the tango logviewer tool  (for local development purpose)
* tangotest.yaml: define a k8s pod for the tangotest device server
* mongodb.yaml: define a k8s service for mongo db and a statefulset attached to it (used by the webjive service)
* rsyslog.yaml: define a k8s service for rsyslog and a statefulset attached to it
* tmcprototype.yaml: define a k8s pod for the tmc-prototype; it contains the following device servers: 
	* dishmaster1 
	* dishmaster2 
	* dishmaster3 
	* dishmaster4 
	* dishleafnode1 
	* dishleafnode2 
	* dishleafnode3 
	* dishleafnode4 
	* subarraynode1 
	* subarraynode2 
	* centralnode 
	* tm-alarmhandler
	* configure-alarms 
	* conf-polling-events
* webjive.yaml: define a k8s service for webjive application and a statefulset attached to it; it contains the following containers: 
	* webjive 
	* authserver 
	* dashboards 
	* tangogql 
	* redis
* webjive-ingresses.yaml: define the ingresses for the web application acconding to the traefik ingress controller
* rsyslog-pv.yaml: define a PersistentVolume and a PersistentVolumeClaim for the service rsyslog (rsyslog.yaml)
* tangodb-pv.yaml: define a PersistentVolume and a PersistentVolumeClaim for the database service (tangodb.yaml)
* webjive-pv.yaml: define a PersistentVolume and a PersistentVolumeClaim for the database service (webjive.yaml)


