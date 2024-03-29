#!/bin/bash

#JSON-path expression to extract the pod name and the list of containers
#{range .items[*]}{.metadata.name} {.spec.containers[*].name}{"\n"} {end}

echo -e "section_start:`date +%s`:throttle[collapsed=true]\r\e[0KOutput Throttling information"
#note that the pod name is stored in 1st variable(pod)
# container(s) name is stored in 2nd variable(containers)
kubectl get pods -n $KUBE_NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name} {.spec.containers[*].name}{"\n"} {end}' |while read -r pod containers; do
     # 2nd variable consist of space seprated container lists, converting it to array
     echo "Pod name: $pod";
     array=($containers);
     #inner loop to iterate over containers for each pod(outer loop)
     for container in "${array[@]}";do
        echo "Container: ${container}";
         kubectl -n $KUBE_NAMESPACE exec -i ${pod} -c "$container" </dev/null --  cat /sys/fs/cgroup/cpu.stat | grep throttled
     done
done
echo -e "section_end:`date +%s`:throttle$1\r\e[0K"
