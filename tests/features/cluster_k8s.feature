Feature: Basic cluster functionality
    Create a pvc with ceph and check it

Background:
    Given a Kubernetes cluster with KUBECONFIG .kube/config 

Scenario: storage class nfss1
    When I create a pvc pvc0 with storage class nfss1, accessModes ReadWriteMany, resources 1Gi
    And I create a config map cfg0 from file resources/hello.conf
    And I create a service srv0 with image nginx (port 80, replicas 3) and volumes pvc0 (read-only false, mount path /usr/share/nginx/html) and cfg0 (mount path /etc/nginx/conf.d)
    And I create a service srv1 with image nginx (port 80, replicas 3) and volumes pvc0 (read-only true, mount path /usr/share/nginx/html) and cfg0 (mount path /etc/nginx/conf.d)
    And I create an ingress ingress0 pointing to service srv0, service port 80
    And I create an ingress ingress1 pointing to service srv1, service port 80
    And the service srv0 is ready
    And the service srv1 is ready
    And I execute the command echo $(date) > /usr/share/nginx/html/index.html on service srv0
    Then a curl with hostname srv0 and srv1 return the same result

Scenario: storage class bds1
    When I create a pvc rbd-pvc with storage class bds1, accessModes ReadWriteOnce, resources 1Gi
    And I create a config map rbd-test from file resources/hello.conf
    And I create a service rbd-nginx1 with image nginx (port 80, replicas 1) and volumes rbd-pvc (read-only false, mount path /usr/share/nginx/html) and rbd-test (mount path /etc/nginx/conf.d)
    And I create an ingress rbd-test pointing to service rbd-nginx1, service port 80
    And the service rbd-nginx1 is ready
    And I execute the command echo $(date) > /usr/share/nginx/html/index.html on service rbd-nginx1
    Then I can curl with hostname rbd-nginx1
