#!/bin/bash

set -e -o pipefail
echo "Smoke test START (expected pods=31)"
expected_pod=31
n=10
while [ $n -gt 0 ]; do 
	n=$(expr $n - 1)
	x=$(kubectl get pods -n integration --field-selector=status.phase=Running | wc -l)
	echo "Running pods=$x"
	if [ $x != $expected_pod ]; then 
    	echo "Waiting for pods to become running..."
		sleep 30s
	fi
	if [ $x == $expected_pod ]; then 
		exit 0
	fi 
done 
exit 1