FROM artefact.skao.int/ska-tango-images-pytango-builder-alpine:0.3.0

ARG POETRY_VERSION=1.2.0a2

RUN apk add --update \
    curl \
    gcc \
    libressl-dev \
    bash \
    openssh \
    musl-dev \
    libffi-dev && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile=minimal && \
    source $HOME/.cargo/env && \
    pip install poetry==${POETRY_VERSION}

COPY --from=bitnami/kubectl:latest /opt/bitnami/kubectl/bin/kubectl /usr/local/bin/kubectl

COPY --from=alpine/helm:latest /usr/bin/helm /usr/local/bin/helm

RUN apk add --update --no-cache bash  gnupg bash-completion openssh

COPY --chown=tango:tango .devcontainer/.bashrc /home/tango/.bashrc

RUN poetry completions bash > /etc/profile.d/poetry.bash-completion

RUN poetry completions bash > /etc/profile.d/poetry.bash-completion

USER tango

RUN mkdir /home/tango/.kube
