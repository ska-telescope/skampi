#!/bin/bash

REPOPATH="docstatus/repos/$1"
DOCPATH="$REPOPATH/docs/Readme.md"

if [ -L "$DOCPATH" ]; then
    echo "=> Readme File exists!"
    exit 1
else
    echo "=> Readme File not found!"
    exit 0
fi
