Helm 
====
Helm is the Kubernetes tool for managing the deployment of k8s resources and dependencies. Charts are packages of pre-configured Kubernetes resources, and before packaged, are nothing more than a collection of directories and yaml files containing all the information required to to create kubernetes resources using a templating language.

For more information on how templating works, please consult the Developer Portal on `templating an application <https://developer.skatelescope.org/en/latest/tools/containers/orchestration-guidelines.html#templating-the-application>`_.

A general tutorial on Kubernetes and Helm in the SKA context was given during the `2021-07 Tango Training sessions <https://confluence.skatelescope.org/display/SE/2021-07-05+Tango+Training>`_, day 3. Feel free to simply go to the `containerisation and orchestration training repository <https://gitlab.com/ska-telescope/sdi/ska-cicd-training-containerisation-and-orchestration>`_.

To familiarise further with the use of Helm charts in the SKA projects, please clone and play around with the |link_tango_examples| repository. There are a few examples of how to develop Tango applications, and for deploying them in any kubernetes cluster, from a local Minikube cluster (for local testing) to a cloud-based cluster. While you're looking around in Tango Examples, take note of the two directories under the `/charts/` folder: `testparent` and `ska-tango-examples`. Make a note of the difference between an umbrella chart and the chart you're developing for your application. The `testparent` chart is an umbrella chart, and installs the necessary dependencies for deploying your new application. The SKAMPI Mid and SKAMPI Low charts are also umbrella charts, and they differ from the `testparent` chart only in that it installs the application directly from the source code (using the `file://../` value for `repository`). In the SKAMPI repository, all your charts are pulled from the centrally hosted Helm repository (in the Central Artifact Repository).

For a more detailed explanation of the Umbrella / subcharts architecture used at SKA, see the section on Helm subcharts in the `orchestration guidelines <https://developer.skatelescope.org/en/latest/tools/containers/orchestration-guidelines.html#helm-sub-chart-architecture>`_.

All the charts are included in the folder "charts". Every chart has the following structure: 

.. code-block:: console

   Chart.yaml          # A YAML file containing information about the chart
   values.yaml         # The default configuration values for this chart
   chart/              # A directory containing any charts upon which this chart depends.
   chart/templates/    # A directory of templates that, when combined with values,
                       # will generate valid Kubernetes manifest files.

.. code-block:: console

   # Chart.yaml
   apiVersion: v1
   appVersion: "1.0"
   description: A Helm chart for deploying the Tango-Base on Kubernetes
   name: ska-tango-base
   version: 0.2.24

.. code-block:: console

   # example of values
   tmcprototype:
    enabled: true
    image:
       registry: artefact.skao.int
       image: tmcprototype
       tag: latest
       pullPolicy: Always


Update chart settings.
----------------------

In some cases you may want to alter the settings applied in the chart.
E.g To set the taranta chart to have 3 replicas of tangogql, update `values.yaml` to the following:

.. code-block:: console

   taranta:
    tangogql:
     replicas: 3

More information available at |link_helm_docs|, and also at the |link_helm_glossary|. 

.. |link_tango_examples| raw:: html

   <a href="https://gitlab.com/ska-telescope/ska-tango-examples/">SKA Tango Examples</a>

.. |link_helm_docs| raw:: html

   <a href="https://helm.sh/docs/">Helm Documentation</a>

.. |link_helm_glossary| raw:: html

   <a href="https://helm.sh/docs/">Helm Glossary</a>
    
