A&A
===
In this folder there is a simple example of authentication and authorization in minikube. To enable authentication with [static file](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#static-password-file) in a minikube environment start it with the following command:
```
sudo -E minikube start --vm-driver=none --extra-config=kubelet.resolv-conf=/var/run/systemd/resolve/resolv.conf --extra-config=apiserver.basic-auth-file=/var/lib/minikube/certs/users.csv
```

There are two possibilities for authorization in k8s: the first one is called RBAC (Role-based access control) and the second one is called ABAC (Attribute-based access control).

RBAC
====

[RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) allows authorization based on the roles of individual users within an enterprise. A role contains a set of rules which define
* an API group (all the k8s api is divided into a set of groups),
* a set of resources like pod, deployment and so on,
* a set of verbs like get, list and so on 

Each role is related to the users with a resource called RoleBinding. The file `roles.yaml` shows an example of Role and RoleBinding which make the user "matteo" able to work (do anything) on the "integration" namespace.

ABAC
====

[ABAC](https://kubernetes.io/docs/reference/access-authn-authz/abac/) allows authorization according to a set of policies which combine attributes together. The authorization policy is specified into a file with format one JSON object per line. Each line is a policy object containing which specify versioning information and specification, for example:

`{"apiVersion": "abac.authorization.kubernetes.io/v1beta1", "kind": "Policy", "spec": {"user": "matteo", "namespace": "integration", "resource": "", "apiGroup": ""}} `

KUBECONFIG
==========

The command `kubectl config view` shows the current configuration of the running minikube instance. In order to reproduce the PoC of this folder it is necessary to modify it adding the context for the user to access the local cluster (the file `kubeconfig` shows how it has been modified). 
More information can be found [here](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)