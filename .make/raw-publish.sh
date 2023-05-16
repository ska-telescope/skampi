#!/bin/bash

set -e
set -o pipefail

RAW_DIR=raw

source .make-metadata-support

#extract metadata
metadataGenerate MANIFEST.skao.int

#patch the metadata to raw artifacts
for LIBRARY in $RAW_DIR/*; do 
    [ -e "$LIBRARY" ] || continue
    echo $LIBRARY
    for file in $LIBRARY/*; do 
        
        ./ska-cicd-makefile/patch-metadata.sh $file MANIFEST.skao.int

        # Set comma as delimiter
        IFS='/'
        #Read the split words into an array based on comma delimiter
        read -a strarr <<< "$LIBRARY"

        echo Pushing to CAR $file
        #upload the OUTPUT collections having metadata to CAR  
        curl -v -u $CAR_RAW_USERNAME:$CAR_RAW_PASSWORD --upload-file $file $CAR_RAW_REPOSITORY_URL/${strarr[1].tar.gz};
    done
done