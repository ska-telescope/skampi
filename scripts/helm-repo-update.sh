#!/bin/bash

pwd
# Change directory to charts/ folder if it exists

if [ -d "charts" ]
then
        cd charts
else
        exit 1
fi

# Ad repo to local env
helm repo add ska-integr8 $RAW_HOST/helm-chart

# Copy repo index to pwd
wget $RAW_HOST/repository/helm-chart/index.yaml

# Package all helm charts inside charts folder
for d in */
do
        helm package "$d"
done

# Update index.yaml
helm repo index --merge index.yaml --url  $RAW_HOST/repository/helm-chart/ .

# Upload all
for f in *.tgz
do
        curl -v -u $RAW_USER:$RAW_PASS --upload-file $f $RAW_HOST/repository/helm-chart/$f
done
curl -v -u $RAW_USER:$RAW_PASS --upload-file index.yaml $RAW_HOST/repository/helm-chart/index.yaml


