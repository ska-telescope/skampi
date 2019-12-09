#!/bin/bash

set -e -o pipefail
echo "Smoke test START"
n=10
while [ $n -gt 0 ]; do 
	waiting=$(kubectl get pods -n integration -o=jsonpath='{.items[*].status.containerStatuses[*].state.waiting.reason}' | wc -w)
	echo "Waiting containers=$waiting"
	if [ $waiting != 0 ]; then 
    	echo "Waiting 30s for pods to become running...#$n"
		sleep 30s
	fi
	if [ $waiting == 0 ]; then 
		echo "Smoke test SUCCESS"
		exit 0
	fi 
	if [ $n == 1 ]; then 
		waiting=$(kubectl get pods -n integration -o=jsonpath='{.items[*].status.containerStatuses[*].state.waiting.reason}' | wc -w)
		echo "Smoke test FAILS"
		echo "Found $waiting waiting containers: "
		kubectl get pods -n integration -o=jsonpath='{range .items[*].status.containerStatuses[?(.state.waiting)]}{.state.waiting.message}{"\n"}{end}'
		exit 1
	fi 
	n=$(expr $n - 1)
done
