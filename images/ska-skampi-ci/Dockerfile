FROM artefact.skao.int/ska-cicd-k8s-tools-build-deploy:0.8.6 as ska_cicd_base

FROM artefact.skao.int/ska-tango-images-pytango-builder:9.3.32

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION="1.3.2"

COPY --from=ska_cicd_base /usr/local/bin /usr/local/bin

# Install poetry as a binary
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3 - --yes
RUN ln -sfn /opt/poetry/bin/poetry /usr/local/bin/poetry


RUN apt-get update && apt-get install -y net-tools jq
