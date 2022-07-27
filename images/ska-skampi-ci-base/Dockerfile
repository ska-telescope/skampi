# This variables is always available and resolves to
# artefact.skao.int/ska-tango-images-pytango-builder-alpine:x.x.x
# Provide it in PrivateRules.mak if needed locally
ARG SKA_K8S_TOOLS_BUILD_DEPLOY_ALPINE
ARG SKA_K8S_TOOLS="${SKA_K8S_TOOLS_BUILD_DEPLOY_ALPINE}"
ARG SKA_PYTHON_PYTANGO_BUILDER_ALPINE_IMAGE
ARG PYTANGO_BASE="${SKA_PYTHON_PYTANGO_BUILDER_ALPINE_IMAGE}"

FROM $SKA_K8S_TOOLS as ska_cicd_k8s_tools
FROM $PYTANGO_BASE as builder

# Get all other dependencies from SKAO Default CI Image
COPY --from=ska_cicd_k8s_tools /usr/local/bin /usr/local/bin

# Install poetry and dependencies
COPY ./poetry.lock* ./pyproject.toml /app/

# Need to ignore installed packages but note that this may be problematic due to versions as we are not really checking them
# This is due to the fact that poetry is install with pip in base images
RUN poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes && \
    pip install --upgrade pip && \
    pip install --ignore-installed -r poetry-requirements.txt && \
    rm poetry-requirements.txt 

LABEL \
    int.skao.application="SKA SKAMPI CI Base Image" \
    int.skao.team="Systems Team" \
    author="SKAO Systems Team" \
    description="This image is used as a base CI Image internally" \
    license="BSD-3-Clause"


