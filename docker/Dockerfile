FROM artefact.skao.int/ska-tango-images-pytango-builder:9.3.32

RUN apt-get update && apt-get install -y openssh-client

RUN curl -sSL https://install.python-poetry.org | python3 -

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

RUN curl curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
