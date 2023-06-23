FROM artefact.skao.int/ska-tango-images-pytango-builder:9.4.1

LABEL \
      author="Pedro Osório Silva <pedro.osorio@atlar.pt>" \
      description="This image contains SKAMPI packages jupyter notebooks and pytest" \
      license="BSD-3-Clause" \
      int.skao.team="Systems Team" \
      int.skao.version="1.0.0" \
      int.skao.repository="https://gitlab.com/ska-telescope/ska-skampi"

RUN apt update && apt install -y --no-install-recommends nodejs npm jq git bash vim
RUN npm install -g configurable-http-proxy
RUN python3 -m pip install --no-cache-dir jupyterhub jupyterlab notebook

RUN curl -L "https://github.com/mikefarah/yq/releases/download/v4.33.3/yq_linux_amd64" -o /usr/bin/yq && \
    curl -L "https://dl.k8s.io/release/v1.26.3/bin/linux/amd64/kubectl" -o /usr/bin/kubectl && \
    curl -L "https://get.helm.sh/helm-v3.11.2-linux-amd64.tar.gz" -o /tmp/helm.tar.gz && \
    curl -L "https://github.com/derailed/k9s/releases/download/v0.27.3/k9s_linux_amd64.tar.gz" -o /tmp/k9s.tar.gz && \
    cd /tmp && \
    tar -xvf /tmp/helm.tar.gz && cp linux-amd64/helm /usr/bin/helm && \
    tar -xvf /tmp/k9s.tar.gz && cp k9s /usr/bin/k9s && \
    chown root:root /usr/bin/yq /usr/bin/kubectl /usr/bin/helm /usr/bin/k9s && \
    chmod 755 /usr/bin/yq /usr/bin/kubectl /usr/bin/helm /usr/bin/k9s

COPY --chown=tango:tango poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install
COPY --chown=tango:tango ./ ./
RUN git config --global --add safe.directory /app && \
    chown -R tango:tango /app

