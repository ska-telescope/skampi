#!/bin/bash

END_TIME=$(( `date +%s --date $CI_PIPELINE_CREATED_AT` + $1 ))
echo Running until `date --date=@$END_TIME`

i=0
while (( `date +%s` < $END_TIME )); do

    # One iteration per 5 minutes maximum
    RATE_LIMIT=$(( `date +%s` + 300 ))
    
    export KUBE_NAMESPACE=$KUBE_NAMESPACE_PREFIX-$i
    export KUBE_NAMESPACE_SDP=$KUBE_NAMESPACE_PREFIX-$i-sdp

    echo === Iteration $i \(namespaces $KUBE_NAMESPACE / $KUBE_NAMESPACE_SDP\) ===
    kubectl delete namespace $KUBE_NAMESPACE $KUBE_NAMESPACE_SDP
    kubectl create namespace $KUBE_NAMESPACE &&
        kubectl create namespace $KUBE_NAMESPACE_SDP && \
        timeout 5m make install && \
        (timeout 10m make k8s_test | grep --line-buffered -E "xfailed|PASSED|FAILED|XFAIL|XPASS|ERROR|\.py::")

    # Move logs
    mkdir -p logs
    mv build logs/$i

    # Clear up afterwards
    kubectl delete namespace $KUBE_NAMESPACE $KUBE_NAMESPACE_SDP &
    i=$((i + 1))

    # Rate limiting
    if (( `date +%s` < $RATE_LIMIT )); then
        TO_DELAY=$(( $RATE_LIMIT - `date +%s` ))
        echo Over rate limit - delaying $TO_DELAY seconds before retry...
        sleep $TO_DELAY
    fi

done
