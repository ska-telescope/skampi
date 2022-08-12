# This variables is always available and resolves to
# artefact.skao.int/ska-tango-images-pytango-builder-alpine:x.x.x
# Provide it in PrivateRules.mak if needed locally
ARG SKA_K8S_TOOLS_BUILD_DEPLOY
ARG SKA_K8S_TOOLS="${SKA_K8S_TOOLS_BUILD_DEPLOY}"
ARG PYTANGO_BASE="registry.gitlab.com/ska-telescope/ska-tango-images/ska-tango-images-pytango:0.1.0-tc-9.3.3-bullseye-dev.ca7852e3e"
FROM $SKA_K8S_TOOLS as ska_cicd_k8s_tools
FROM $PYTANGO_BASE AS requirements-stage

# Install poetry and dependencies
COPY ./poetry.lock* ./pyproject.toml /app/

# Need to ignore installed packages but note that this may be problematic due to versions as we are not really checking them
# This is due to the fact that poetry is install with pip in base images
RUN poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes --dev

FROM $PYTANGO_BASE

LABEL \
    int.skao.application="SKA SKAMPI CI Base Image" \
    int.skao.team="Systems Team" \
    author="SKAO Systems Team" \
    description="This image is used as a base CI Image internally" \
    license="BSD-3-Clause"

# Install runtime dependencies (copied over from SKA_K8S_TOOLS_BUILD_DEPLOY)
RUN apt-get update && \
    apt-get install -y \
    apt-transport-https \
    bash \
    ca-certificates \
    curl \
    git \
    git-lfs \
    make \
    g++ \
    cmake \
    rpm \
    software-properties-common \
    wget \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

RUN sudo mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    docker-ce \
    docker-ce-cli \
    jq \
    net-tools \
    ssh \
    unzip \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Get all other dependencies from SKAO Default CI Image
COPY --from=ska_cicd_k8s_tools /usr/local/bin /usr/local/bin

COPY --from=requirements-stage /app/poetry-requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --upgrade -r poetry-requirements.txt && \
    rm poetry-requirements.txt 

