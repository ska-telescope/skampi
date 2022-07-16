# This variables is always available and resolves to
# artefact.skao.int/ska-tango-images-pytango-builder-alpine:x.x.x
# Provide it in PrivateRules.mak if needed locally
ARG SKA_K8S_TOOLS_BUILD_DEPLOY_ALPINE
ARG SKA_CI_BASE="${SKA_K8S_TOOLS_BUILD_DEPLOY_ALPINE}"
ARG SKA_PYTHON_PYTANGO_BUILDER_IMAGE
ARG PYTANGO_BASE="${SKA_PYTHON_PYTANGO_BUILDER_IMAGE}"

FROM $SKA_CI_BASE as ska_cicd_k8s_tools

FROM $PYTANGO_BASE as builder

# Get all other dependencies from SKAO Default CI Image
COPY --from=ska_cicd_k8s_tools /usr/local/bin /usr/local/bin

# Install poetry and dependencies
RUN poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes && \
    pip install -r poetry-requirements.txt && \
    rm poetry-requirements.txt 

LABEL \
    int.skao.application="SKA SKAMPI CI Base Image" \
    int.skao.team="Systems Team" \
    author="SKAO Systems Team" \
    description="This image is used as a base CI Image internally" \
    license="BSD-3-Clause"


