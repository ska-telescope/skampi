#!/bin/bash

set -e -o pipefail
echo "pipefail set"
sleep 4m
x=$(kubectl get pods -n integration --field-selector=status.phase=Running | wc -l)
echo "$x"
if [ $x != "31" ]; then
	echo "not all pods are running"
	exit 1

fi
