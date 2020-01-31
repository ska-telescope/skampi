#!/bin/bash

if [ "$(helm repo list | grep nexus)" != "" ]
then
	echo yes
fi
