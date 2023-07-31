FROM artefact.skao.int/ska-cicd-k8s-tools-build-deploy:0.8.6 as ska_cicd_k8s_tools

FROM artefact.skao.int/ska-tango-images-pytango-builder:9.3.32

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION="1.3.2"

COPY --from=ska_cicd_k8s_tools /usr/local/bin /usr/local/bin

RUN curl -sSL https://install.python-poetry.org | python3 -
#RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py --output $POETRY_HOME/install-poetry.py
#RUN cd $POETRY_HOME && POETRY_VERSION=${POETRY_VERSION} python3 install-poetry.py --yes
RUN ln -sfn /opt/poetry/bin/poetry /usr/local/bin/poetry


RUN apt-get update && apt-get install -y net-tools jq


RUN poetry config virtualenvs.in-project true

RUN pip install virtualenv

RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

USER tango

# place pytango wheel in a directory that can be accessed by poetry

#RUN pip wheel pytango --wheel-dir $HOME/.wheels/

RUN python3 -m pip install black flake8 pre-commit isort

RUN python3 -m pip install --no-cache-dir notebook jupyterlab

RUN poetry config virtualenvs.in-project true

RUN pip install virtualenv

RUN https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

ENTRYPOINT ["/bin/bash"]

