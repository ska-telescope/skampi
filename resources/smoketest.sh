#!/bin/bash

echo "hello"

set -e -o pipefail
echo "pipefail set"

x = "$(kubectl get pods -n integration --field-selector=status.phase=Running | wc -l)"
echo "x is set"
echo "$x"

if [ "$x" != "2" ]; then
	exit 1

fi
