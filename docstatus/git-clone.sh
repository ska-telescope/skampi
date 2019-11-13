#!/bin/bash

#BASEURL="https://gitlab.com/ska-telescope/" #HTTPS
BASEURL="git@gitlab.com:ska-telescope/" #SSH
REPOPATH=$1
DOCSPATH="$REPOPATH/docs"
REPOURL="${BASEURL}$1.git"

if [ ! -d "$REPOPATH" ]; then
  git clone "$REPOURL"
  if [ -d "$DOCSPATH" ]; then
    exit 1
  fi
#  exit 0
else
  cd $REPOPATH && git pull
  if [ -d "docs" ]; then
    exit 1
  else
    exit 0
  fi
fi

