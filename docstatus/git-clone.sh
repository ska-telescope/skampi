#!/bin/bash

#BASEURL="https://gitlab.com/ska-telescope/" #HTTPS
BASEURL="git@gitlab.com:ska-telescope/" #SSH
REPOPATH=$1
REPOURL="${BASEURL}$1.git"
if [ -d "$REPOPATH" ]; then
  exit 1
else
  git clone "$REPOURL"
  if [ -d "$REPOPATH" ]; then
    exit 1
  fi
  exit 0
fi

