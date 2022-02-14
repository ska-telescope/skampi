SKAMPI - SKA Mvp Prototype Integration
======================================

SKAMPI is the SKA repository containing the software products and related integration tools for releasing these products developed by the SKA Software development teams and which are required to run the SKA telescope.

The Makefiles, scripts, test infrastructure and other resources allow for the deployment of a suite of software products for testing and integration, including hardware integration.

SKAMPI consists of a set of helm charts that each deploy a software component or set of components in a kubernetes environment. SKAMPI can thus be deployed in a variety of ways, and the best way to deploy or interact with SKAMPI will depend on what you need to do with it.  For advice on running SKAMPI, ask on the `#proj-mvp Slack channel <https://skao.slack.com/archives/CKBDRGCKB>`_.

SKAMPI and its components are being actively developed, and can change rapidly. As components are updated, the SKAMPI helm charts will also be updated to allow use of the updated component.

To see a list of the GitLab projects used to develop SKAMPI components, and find the associated documentation, `SKAMPI projects are listed on the developer portal </projects/area.html#skampi>`_.
You can also see a `deployment diagram for SKAMPI <https://confluence.skatelescope.org/pages/viewpage.action?pageId=105415493>`_.

.. toctree::
   :maxdepth: 2

   README

.. toctree::
   :maxdepth: 1

   deployment
   subsystems
   testing
   integrating
   