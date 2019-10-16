Environments
============

Two environments has been defined for the SKAMPI repository, namely "test" and "staging", both deployed into a k8s cluster linked in the Gitlab.

Test environment
----------------
In the test environment, the helm chart pull policy for the docker images must be “Always” and the image tag must be "latest". A trigger must be defined for every Gitlab repository so that when the pipeline succeeded, it triggers the pipeline of the SKAMPI repository. 

The branch for this environment is the master. 

A trigger example is the following one: 

.. code-block:: console

  trigger: 
    image: appropriate/curl 
    stage: trigger 
    tags: 
    - docker-executor 
    script: 
        - curl -X POST -F token=$SKAMPI_TOKEN -F ref=$SKAMPI_TARGET_BRANCH https://gitlab.com/api/v4/projects/$SKAMPI_PROJ_ID/trigger/pipeline

This will make obtain the following advantages:

* A successful commit (that is the pipeline succeeded) in a sub-project repository (like the tmc-prototype) starts the deployment in the integration environment for all the containers defined in the helm chart. 
* Update of the integration environment happens continuously
* Teams won’t care about releases

Staging environment
-------------------
In the staging environment, the helm chart pull policy for the docker images must be “IfNotPresent” and the image tag must be a specific version. The pipeline of the SKAMPI repository will be triggered by a change in an helm chart. 

The branch for this environment is the staging. 