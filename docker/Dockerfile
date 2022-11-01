FROM artefact.skao.int/ska-cicd-k8s-tools-build-deploy:0.7.3 as ska_cicd_k8s_tools

FROM artefact.skao.int/ska-tango-images-pytango-builder:9.3.32

COPY --from=ska_cicd_k8s_tools /usr/local/bin /usr/local/bin