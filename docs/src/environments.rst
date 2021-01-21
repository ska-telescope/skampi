Environments
============


.. Note::

    Note that kubernetes is essential a client server architecture in which the control plane is accessed by a client process. Thus even if you run Minikube you still use
    the client (with credentials automatically set up for you) to command the actual k8 environment. The skampi makefile targets assume you have a working client that has access to some
    kind of environment. You can therefore 'point' your client to different environments according to what your intentions will be.

Viewed as stages in a delivery pipeline, the intended target environment types are defined as follows (ordered from downstream to upstream stages):

-   **On site Integration:** A version deployed on a particular site that includes 
    actual telescope hardware (or hardware prototypes) to perform site integration 
    tests
-   **Staging:** A fixed version released at particular points in time (mostly every 
    PI sprint), made accessible via a set of web URLs for users wanting to demonstrate
    or explore current delivered value.
-   **Pipeline Testing:** A version automatically deployed as a result of a new 
    commit on a branch of SKAMPI in order to run the predefined continuous integration
    tests.
-   **Integration Testing:** A platform exactly the same as for staging in which 
    the user has manual control over the version of SKAMPI and the instantiating of it's
    deliverables so as to test during development of new features
-   **Development:** A miscellaneous set of platforms (e.g. K8 minikube, K3) with separate
    self standing clusters that allows a developer to simulate the target environment
    in order to have close control over the composition and life cycle of SKAMPI parts
    during development

**On Site Integration:**
Currently there is only a platform for the Low instance (PSI Low).

**Staging:**
The following URLs can be used to access the deployed instances:

    - `ska mid <https://staging.engageska-portugal.pt/staging-mid>`_ 
    - `ska low <https://staging.engageska-portugal.pt/staging-mid>`_ 

**Pipeline Testing:**
For each branch (including master) git lab ci provides a deployed instance of mid and low.
To view the status of pipelines, use the following `link <https://gitlab.com/ska-telescope/skampi/-/pipelines>`_.
A user can also run a pipeline `manually <https://gitlab.com/ska-telescope/skampi/-/pipelines/new>`_ and set env variables to run
the pipeline in a specific configuration. For example, to run a pipeline on a deployment in which an entire instance is deleted
then re-deployed, set the env var *DELETE* = *true*.

**Integration Testing:**
For integration testing a group of users are provided with a dedicated K8 namespace within the cluster to perform
tests and integration activities on. A set of credentials and certificates are provided in the form of a kubefonfig file
that provides the owner of the certificates freedom to perform any operation on software as long as it is confined within 
that namespace. 

The following namespaces are currently set up for integration testing:

.. csv-table:: 
   :header: "Namespace", "Purpose", "Notes"
   :widths: 20, 60, 60

   "team-mvp", "End to end testing of integrated product", "Contact systems team for credentials"

**Development:**
Various options are available to set up a develop environment and is mostly determined by the number of active workloads (pods, jobs etc) 
that is needed to run during development. A normal SKA mid deployment typically consume equivalent nr of resources for at least two standard laptops.
Thus a developer will need to subset the deployment accordingly to what his environment can provide. Minikube is very useful to provide a K8 env contained
within a virtual machine running on your local laptop and provide the same behavior as long as the resources stayed withing that of what your VM can provide.
Another option is to make use of a dedicated server or clusters and provide credentials to a group of developers for accessing the cluster. 
