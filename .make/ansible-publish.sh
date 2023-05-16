#!/usr/bin/env bash

set -e
set -o pipefail

OUTPUT=ansible-collections

#create a directory for OUTPUT collections along with directory structure if it doesn't exist
mkdir -p $OUTPUT

#build the collections
ansible-galaxy collection build --force --output-path=$OUTPUT \
	$COLLECTIONS

#enter OUTPUT directory
cd ${OUTPUT}

#extract metadata
if [ ! -f /usr/local/bin/extract-metadata.sh ]; then
    curl https://gitlab.com/ska-telescope/ska-k8s-tools/-/raw/master/docker/deploy/scripts/extract-metadata.sh -o extract-metadata.sh && chmod +x extract-metadata.sh
    ./extract-metadata.sh MANIFEST.skao.int
else
    /usr/local/bin/extract-metadata.sh MANIFEST.skao.int
fi

#patch the metadata to ansible collections
for collection in $COLLECTIONS; do
file=$(find . -name "*$collection*.tar.gz")
echo $file
/usr/local/bin/patch-ansible-metadata.sh $file MANIFEST.skao.int
done

#upload the OUTPUT collections having metadata to CAR
for f in *.tar.gz; do
curl -v -u $CAR_ANSIBLE_USERNAME:$CAR_ANSIBLE_PASSWORD --upload-file $f $CAR_ANSIBLE_REPOSITORY_URL/$f;
echo $f
rm $f;
done