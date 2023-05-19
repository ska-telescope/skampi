FROM artefact.skao.int/ska-cicd-k8s-tools-build-deploy:0.8.6 as ska_cicd_base

FROM artefact.skao.int/ska-tango-images-pytango-builder:9.3.32

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION="1.3.2"

COPY --from=ska_cicd_base /usr/local/bin /usr/local/bin

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py --output $POETRY_HOME/install-poetry.py
RUN cd $POETRY_HOME && POETRY_VERSION=${POETRY_VERSION} python3 install-poetry.py --yes
RUN ln -sfn /opt/poetry/bin/poetry /usr/local/bin/poetry


RUN apt-get update && apt-get install -y net-tools jq
