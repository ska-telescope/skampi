#!/bin/bash

#BASEURL="https://gitlab.com/ska-telescope/" #HTTPS
BASEURL="git@gitlab.com:ska-telescope/" #SSH
REPOPATH=$1
REPOURL="${BASEURL}$1.git"
git clone "$REPOURL"
if [ -d "$REPOPATH" ]; then
  echo 1
else
  echo 0
fi

echo $REPOPATH