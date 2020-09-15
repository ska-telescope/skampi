#!/bin/bash

ls -la
[[ -d charts ]] || (ls -la && echo "No charts directory found" && exit 1);

# # install helm
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh

# create clean repo cache dir
[[ -d "chart-repo-cache" ]] && rm -rf chart-repo-cache
mkdir chart-repo-cache

# add SKA Helm Repository
helm repo add skatelescope $HELM_HOST/repository/helm-chart --repository-cache chart-repo-cache
helm repo list
helm repo update
helm search repo skatelescope

# Package charts
[ -z "$CHARTS_TO_PUBLISH" ] && export CHARTS_TO_PUBLISH=$(ls -d charts/*/)
for chart in $CHARTS_TO_PUBLISH; do
  echo "######## Packaging $chart #########"
  helm package "$chart" --destination chart-repo-cache
done

# rebuild index
helm repo index chart-repo-cache --merge chart-repo-cache/cache/skatelescope-index.yaml
for file in chart-repo-cache/*.tgz; do
  echo "######### UPLOADING ${file##*/}";
  curl -v -u $HELM_USERNAME:$HELM_PASSWORD --upload-file ${file} $HELM_HOST/repository/helm-chart/${file##*/}; \
done
curl -v -u $HELM_USERNAME:$HELM_PASSWORD --upload-file chart-repo-cache/index.yaml $HELM_HOST/repository/helm-chart/${file##*/}; \

helm search repo skatelescope >> chart-repo-cache/before
sleep 2
helm repo update
helm search repo skatelescope >> chart-repo-cache/after
helm search repo skatelescope

echo "This publishing step brought about the following changes"
diff chart-repo-cache/before chart-repo-cache/after --color

rm -rf chart-repo-cache
