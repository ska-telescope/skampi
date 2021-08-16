#
# This Dockerfile creates a Docker image intended to be a for development work in a local environment
# it comes with the neccesarry dependencies to run pytango in python 3.7 as well as 
# additional depepencies to enable a user to work in a vscode IDE environment and connect remotely
# to a kubernetes cluster to perform end to end tests.
#

FROM nexus.engageska-portugal.pt/test-alpine-tango-images/builder:0.1.1

COPY --from=bitnami/kubectl:latest /opt/bitnami/kubectl/bin/kubectl /usr/local/bin/kubectl

COPY --from=alpine/helm:latest /usr/bin/helm /usr/local/bin/helm

RUN apk add --update --no-cache bash openssh iputils

COPY --chown=tango:tango .devcontainer/.bashrc /home/tango/.bashrc

RUN pip install six==1.16.0

COPY .devcontainer/vscode_requirements.txt .devcontainer/test_requirements.txt ./

RUN pip install -r vscode_requirements.txt -r test_requirements.txt && rm vscode_requirements.txt && rm test_requirements.txt

RUN git clone -q http://github.com/datawire/telepresence && cd telepresence && git checkout release/v1 && PREFIX=/usr ./install.sh && rm -r telepresence

USER tango

RUN mkdir /home/tango/.kube