Helm 
====
Helm is a tool for managing Kubernetes charts. Charts are packages of pre-configured Kubernetes resources.

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
E.g To set the webjive chart to have 3 replicas of tangogql, update `values.yaml` to the following:

.. code-block:: console

   webjive:
    tangogql:
     replicas: 3
    
More information available `here <https://helm.sh/docs/>`_. 
Helm Glossary here <https://helm.sh/docs/glossary/>`_. 