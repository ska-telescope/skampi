.. _remote_host:

Deploying SKAMPI components on mid-itf
**************************************

Adding yaml file to deploy to mid-itf
=====================================

Adding a mid-itf-values.yaml file containing SKAMPI components that needs to be deployed
to the mid-itf. The `'minikube: false'` field specifies persistent volume claims are not going to be satisfied, in this case mid-itf facility.

Each component listed in the file will have enabled field set to true if it is to be deployed, 
it will be false otherwise. An example below deploys ska-mid-cbf:
.. code-block:: console
    ska-mid-cbf:
    enabled: true

Including `'the mid-itf-values.yaml'` to the pipelines.
=======================================================

In order for the mid-itf-values.yaml file contents to be consumed by gitlab pipelines it needs to be
included in the gitlab pipelines configuration file.

We modify the mid-itf.gitlab-ci.yml file under .gitlab/ci by adding the mid-itf-values.yaml file link
to the VALUES parameter. The line below shows the `'ska-mid-cbf'` file added to VALUES field.
.. code-block:: console
    VALUES: "charts/ska-$CONFIG/$CONFIG-itf-values.yaml"


Using gitlab environment variables
---------------------------------

It is recommended to use gitlab environment variables as much as possible and to avoid hard coding pipelines.
:download:`This link <https://docs.gitlab.com/ee/ci/variables/predefined_variables.html>` is a gitlab official
page with all environment variables that can be used when making changes to gitlab .yml files.