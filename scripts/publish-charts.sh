#!/bin/bash

[ -d charts ] || echo "No charts directory found";

# create clean repo cache dir
[ -d "chart-repo-cache" ] || rm -rf chart-repo-cache;
mkdir chart-repo-cache;

# add SKA Helm Repository
helm repo add skatelescope $HELM_HOST/repository/helm-chart --repository-cache chart-repo-cache
helm repo list
helm repo update
helm search repo skatelescope

# Package charts
for chart in charts/*/
do
  echo "$chart"
  helm package "$chart" --destination chart-repo-cache
done

# rebuild index
helm repo index chart-repo-cache --merge chart-repo-cache/cache/skatelescope-index.yaml
for file in chart-repo-cache/*.tgz; do
  echo "######### uploading ${file##*/}";
  curl -v -u $HELM_USERNAME:$HELM_PASSWORD --upload-file ${file} $HELM_HOST/repository/helm-chart/${file##*/}; \
done
curl -v -u $HELM_USERNAME:$HELM_PASSWORD --upload-file chart-repo-cache/index.yaml $HELM_HOST/repository/helm-chart/${file##*/}; \

helm search repo skatelescope >> chart-repo-cache/before
helm repo update
helm search repo skatelescope >> chart-repo-cache/after

echo "This publishing step brought about the following changes"
diff chart-repo-cache/before chart-repo-cache/after --color

rm -rf chart-repo-cache
