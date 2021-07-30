SKAMPI - SKA Mvp Prototype Integration
======================================

Welcome to skampi! SKAMPI is a software product that integrates the software components needed to run an SKA telescope. 
Skampi thus allows the deployment of a suite of software products for testing and integration, including hardware integration. 

Skampi consists of a set of helm charts that each deploy a software component or set of components in a kubernetes environment. Skampi can thus be deployed in a variety of ways, and the best way to deploy or interact with skampi will depend on what you need to do with it.  For advice on running skampi, ask on the `#proj-mvp Slack channel <https://skao.slack.com/archives/CKBDRGCKB>`_.
You can also look at our Quickstart Guide (TODO), which covers the common use cases of using skampi as a developer, or as a Feature Owner (FO) or AIV (Assembly, Integration and Verification) engineer.

Skampi and its components are being actively developed, and can change rapidly. As components are updated, the skampi helm charts will also be updated to allow use of the updated component. 

To see a list of the GitLab projects used to develop skampi components, and find the associated documentation, `skampi projects are listed on the developer portal </projects/area.html#skampi>`_.
You can also see a `deployment diagram for skampi <https://confluence.skatelescope.org/pages/viewpage.action?pageId=105415493>`_.

.. toctree::
   :maxdepth: 2

   README

.. toctree::
   :maxdepth: 1

   multitenancy
   kubernetes
   helm
   subsystems
