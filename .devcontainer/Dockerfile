#FROM registry.gitlab.com/ska-telescope/ska-skampi/ska-skampi-ci-base:0.1.0
FROM artefact.skao.int/ska-tango-images-pytango-builder:9.3.32

RUN apt-get update && apt-get install -y openssh-client graphviz

RUN curl -sSL https://install.python-poetry.org | python3 -

RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

USER tango

# place pytango wheel in a directory that can be accessed by poetry

# RUN pip wheel pytango --wheel-dir $HOME/.wheels/

RUN python3 -m pip install black flake8 pre-commit isort

RUN python3 -m pip install --no-cache-dir notebook jupyterlab

RUN poetry config virtualenvs.in-project true

RUN pip install virtualenv

RUN https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

ENTRYPOINT ["/bin/bash"]

