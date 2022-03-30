Deploying to Prototype System Integration (PSI) environments
============================================================

PSI clusters exist to support early integration testing of software and some hardware. PSI Low is hosted in the ATNF facility in Marsfield, NSW, and as of March 2022, hardware for PSI Mid is currently being acquired. More information on PSI Low can be found `in Confluence <https://confluence.skatelescope.org/display/SWSI/PSI+Low+Deployment+and+Operations>`_.

SKAMPI may be deployed to PSI Low on demand, through GitLab pipelines. These pipeline jobs are defined in `.gitlab/ci/psi-low.gitlab-ci.yml`. Using these jobs, SKAMPI may be deployed to the following namespaces in the PSI Low cluster:

* from `master` branch to the `integration-low` namespace
* from feature branches to `ci-ska-skampi-<branch-name>-low`
* from git tags to `staging-low`


Using real hardware in PSI deployments
--------------------------------------

The PSI Low hosts specialised hardware, both off-the-shelf and proprietary to SKA. Currently this includes

* LOW telescope subrack and tile processing modules (TPM)
* GPUs for fast parallel computation
* FPGAs for specialised hardware-accelerated computation
* High-performance network interfaces

These devices are exposed in Kubernetes as `extended resources <https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#extended-resources>`_. To use extended resources, a container must declare them in the `resources:limits` field in its spec `as described in the Kubernetes documentation <https://kubernetes.io/docs/tasks/configure-pod-container/extended-resource/>`_.

In order for a SKAMPI component to include these resource requests, its Helm chart has to have fields in its values file for specifying resource requests, which can then be provided in the PSI Low values file at `resources/deployment_configurations/psi-low.yaml`. This file is included in GitLab CI deployments to PSI Low.

Components which use the Tango device server templates in `ska-tango-util <https://gitlab.com/ska-telescope/ska-tango-images/-/tree/master/charts/ska-tango-util/templates>`_ already support this. For example, to specify that ska-low-mccs' tile devices need access to a TPM, this file would include:

.. code-block:: yaml

    ska-low-mccs:
      deviceServers:
        tiles:
          resources:
            limits:
              skao.int/tpm: 1

Depending on the component, you may need to expose more fields in your values file. For example, some components include a toggle to switch between simulated mode and real hardware mode.
