Creating a K8s Web UI Dashboard
===============================

The resources available in this folder enable to create a dashboard (locally available on port 8001) for testing purpose. 

The following lines are the commands to run to create it: 
```
// create dashboard and add an admin user:
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/aio/deploy/recommended/kubernetes-dashboard.yaml
kubectl apply -f dashboard-adminuser.yaml

// to access the dashboard it is needed a secret token
kubectl -n kube-system get secret
kubectl -n kube-system describe secret *token* // default generally called default-token-*****

kubectl proxy
```

More information on https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/

It is also included an example of graphql query for the webjive application. The graphQl Engine is available in the following path of the integration web server: /gql/graphiql/
