FROM artefact.skao.int/ska-cicd-k8s-tools-build-deploy:0.8.6 as ska_cicd_k8s_tools

FROM artefact.skao.int/ska-tango-images-pytango-builder:9.3.32

COPY --from=ska_cicd_k8s_tools /usr/local/bin /usr/local/bin
COPY --from=ska_cicd_k8s_tools /opt/poetry /opt/poetry

RUN ln -sfn /opt/poetry/bin/poetry /usr/local/bin/poetry

RUN apt-get update && apt-get install -y net-tools jq
