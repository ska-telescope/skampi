#!/bin/bash

echo -e "section_start:`date +%s`:throttle[collapsed=true]\r\e[0KOutput Throttling information"
PODS=$(kubectl get pods -n $KUBE_NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | wc -l)
echo -e "Checking $PODS Pods of namespace '$KUBE_NAMESPACE' for throttling:"
kubectl get pods -n $KUBE_NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name} {.spec.containers[*].name}{"\n"} {end}' | while read -r pod containers; do
     POD_CONTAINERS=($containers);
     for CONTAINER in "${POD_CONTAINERS[@]}"; do
          THROTTLED=$(kubectl -n $KUBE_NAMESPACE exec -qi ${pod} -c "$CONTAINER" </dev/null -- sh -c \
               'if [ -f /sys/fs/cgroup/cpu.stat ]; then grep -s -i nr_throttled /sys/fs/cgroup/cpu.stat | sed "s#.* ##"; else echo '0'; fi;' \
          )
          if [ $? -eq 0 ]; then
               if [ $THROTTLED -gt 0 ]; then
                    echo "Container '$CONTAINER' from Pod '$pod' was throttled:";
                    kubectl -n $KUBE_NAMESPACE exec -i ${pod} -c "$CONTAINER" </dev/null --  grep -s -E "(nr_throttled|nr_periods)" /sys/fs/cgroup/cpu.stat
               fi
          else
               echo "Failed to get throttling information on '$CONTAINER' from Pod '$pod'"
          fi
     done
done

echo -e "section_end:`date +%s`:throttle$1\r\e[0K"
