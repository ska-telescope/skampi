Environments
============

Two environments has been defined for the SKAMPI repository, namely "test" and "staging", both deployed into a k8s cluster linked in the `Gitlab <https://gitlab.com/ska-telescope/skampi/-/clusters>`_.

Those are visible in gitlab at this `link <https://gitlab.com/ska-telescope/skampi/-/environments>`_ and managed with schedule in the gitlab schedule `tab <https://gitlab.com/ska-telescope/skampi/pipeline_schedules>`_. 

Test environment
----------------
The test environment is deployed at every commit of the skampi repository. Every day it is scheduled a clean job (at 4 UTC am) ehich redeploy the entire project. 

The primary ingress of this environment is the following link: http://integration.engageska-portugal.pt/

Staging environment
-------------------
Staging environment is deployed only with scheduled job every 15 days. 