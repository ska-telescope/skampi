FROM artefact.skao.int/ska-cicd-k8s-tools-build-deploy:0.8.7 as ska_cicd_k8s_tools

FROM artefact.skao.int/ska-tango-images-pytango-builder:9.4.1

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION="1.3.2"

COPY --from=ska_cicd_k8s_tools /usr/local/bin /usr/local/bin

# Install poetry as a binary
RUN curl -sSL https://install.python-poetry.org | python3 - --yes
RUN ln -sfn /opt/poetry/bin/poetry /usr/local/bin/poetry


RUN apt-get update && apt-get install -y net-tools jq make
