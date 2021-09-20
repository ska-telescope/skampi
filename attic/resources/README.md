Creating a K8s Web UI Dashboard
===============================

The resources available in this folder enable to create a dashboard (locally available on port 8001) for testing purpose. 

The following lines are the commands to run to create it: 
```
// create dashboard and add an admin user:
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/aio/deploy/recommended/kubernetes-dashboard.yaml

// to access the dashboard it is needed a secret token
kubectl -n kube-system get secret
kubectl -n kube-system describe secret *token* // default generally called default-token-*****

kubectl proxy
```

More information on https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/

It is also included an example of graphql query for the webjive application. The graphQl Engine is available in the following path of the integration web server: /gql/graphiql/

Traefik
=======
It is possible to install traefik in different ways: 

```
# Install using tiller
helm install stable/traefik --name traefik0 --namespace kube-system --set externalIP=xxx.xxx.xxx.xxx

# or Install traefik controller manually (deprecated)
kubectl apply -f traefik-minikube.yaml

# Install using the Makefile
make traefik EXTERNAL_IP=xxx.xxx.xxx.xxx

```

Note that the external ip should be the internal ip of the machine. 

Ingress controller commands
===========================
```
# The controller is in the kube-system namespace
kubectl get pods -n kube-system
kubectl logs -n kube-system *nginx-ingress-controller-name*
kubectl exec -it -n kube-system *nginx-ingress-controller-name* cat /etc/nginx/nginx.conf
```