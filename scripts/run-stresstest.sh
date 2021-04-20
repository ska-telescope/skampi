#!/bin/bash

END_TIME=$(( `date +%s --date $CI_PIPELINE_CREATED_AT` + $1 ))
echo Running until `date --date=@$END_TIME`

i=0
while (( `date +%s` < $END_TIME )); do
    
    export KUBE_NAMESPACE=$KUBE_NAMESPACE_PREFIX-$i
    export KUBE_NAMESPACE_SDP=$KUBE_NAMESPACE_PREFIX-$i-sdp

    echo === Iteration $i \(namespaces $KUBE_NAMESPACE / $KUBE_NAMESPACE_SDP\) ===
    curl -s https://gitlab.com/ska-telescope/templates-repository/-/raw/master/scripts/namespace_auth.sh | bash -s $SERVICE_ACCOUNT $KUBE_NAMESPACE $KUBE_NAMESPACE_SDP    
    kubectl delete namespace $KUBE_NAMESPACE $KUBE_NAMESPACE_SDP
    kubectl create namespace $KUBE_NAMESPACE &&
        kubectl create namespace $KUBE_NAMESPACE_SDP && \
        make install && \
        make smoketest && \
        make k8s_test
    sleep 1

    # Move logs
    mkdir -p logs
    mv build logs/$i
    
    kubectl delete namespace $KUBE_NAMESPACE $KUBE_NAMESPACE_SDP &
    i=$((i + 1))
done
