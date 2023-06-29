SKAMPI - SKA MVP Prototype Integration Tests
============================================

SKAMPI is the integration product of the various SKA software components, that compose the SKA Telescope. What originally was a deployment and testing repository, was split into two repositories: `build/deploy <https://developer.skao.int/projects/ska-skampi-deployment/en/latest/index.html>`_ and testing. Together they still support the deployment, testing and release of software created by the SKA Software development teams and which are required to run the SKA Telescope.

The Makefiles, scripts, test infrastructure and other resources allow for the testing a suite of software products and its integration with hardware.

SKAMPI consists of a set of helm charts that each deploy a software component or set of components in a Kubernetes cluster. SKAMPI can thus be deployed in a variety of ways, and the best way to deploy or interact with SKAMPI will depend on what you need to do with it. This holds true for the type of testing you need to do. For advice on working with SKAMPI, ask on the `#proj-mvp Slack channel <https://skao.slack.com/archives/CKBDRGCKB>`_.

SKAMPI and its components are being actively developed, and can change rapidly. As components are updated, the SKAMPI helm charts will also be updated to allow use of the updated component. The tests should also follow the deployment of software, as that is the only way we can reach stability.

To see a list of the GitLab projects used to develop SKAMPI components, and find the associated documentation, `SKAMPI projects are listed on the developer portal </projects/area.html#skampi>`_.
You can also see a `deployment diagram for SKAMPI <https://confluence.skatelescope.org/pages/viewpage.action?pageId=105415493>`_.

.. toctree::
   :maxdepth: 2

   README

.. toctree::
   :maxdepth: 1

   testing
   pipelines
   subsystems
   integrating
   
