ARG SKA_PYTHON_PYTANGO_BUILDER_IMAGE="artefact.skao.int/ska-tango-images-pytango-builder:9.3.35"
ARG SKA_K8S_TOOLS_BUILD_DEPLOY="artefact.skao.int/ska-cicd-k8s-tools-build-deploy:0.8.6"

FROM $SKA_K8S_TOOLS_BUILD_DEPLOY as ska_cicd_k8s_tools

FROM $SKA_PYTHON_PYTANGO_BUILDER_IMAGE

COPY --from=ska_cicd_k8s_tools /usr/local/bin /usr/local/bin

RUN apt-get update && apt-get install -y net-tools jq
