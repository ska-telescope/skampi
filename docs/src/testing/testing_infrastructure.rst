.. _`Testing Runway`:

Basic BDD test to check if Test Results are uploading to Xray
*************************************************************

Refer to ``tests/features/xray_upload.feature`` and ``tests/unit/test_xray_upload.py``. These two tests should give a developer new to BDD testing as well as uploading test results to Xray a running start, however, it will also be required to study the `Skallop documentation on uploading test results to Xray <https://developer.skao.int/projects/ska-ser-skallop/en/latest/howto/use_xtp_upload.html#how-to-configure-xtp-uploading>`_:

Run ``test_xray_upload.py`` and use the pytest paramters to generate the cucumber.json report (recall that you can inspect a ``make`` target's contents by running it with a "dry-run" option, for instance ``make python-test --dry`` will output the commands that will be executed along with all the substituted variables in place).

.. code-block:: console

    $ make python-test CLUSTER_TESTS=skip PYTHON_VARS_AFTER_PYTEST="tests/unit -m infra" #this will only run the one test

Upload the test results using the make target (refer to the Skallop documentation for details on connection and the use of the ``test-exec.json`` file for info on the Test Execution). NOTE: the value for {"versions":[{"maps_to": {"master":<value>}}]} should be changed at the PI boundaries - see the test that checks if this local version is in sync with the Earliest Unreleased version in Jira.

.. code-block:: console

    $ make skampi-upload-test-results 
    Processing XRay uploads
    Processing XRay upload of: build/cucumber.json
    Using Jira Username and Password for auth
    test results uploaded to XTP-6054: https://jira-test.skatelescope.org/browse/XTP-6054


Testing SKAMPI using the Testing Runway (SKALLOP)
*************************************************

.. todo:: step by step instructions to follow.

Integration tests (tests that verify end to end behaviour involving one or more components) are done in BDD
cucumber style using to a large degree fixtures and helper functions coming from skallop repo. 

These tests are defined in terms of two domains:

1. Test control and orchestration (bdd step functions using automatic setup and teardown from skallop)
2. Test domain logic based on the particular "entry point" in which the testing script exercises the SUT

The link between 1 and 2 is based on the concept of an abstract (and stateless) object capable of performing
generric control commands on the SUT. Therefore the concrete instance of this object id determined by the domain
logic or the model of the system when looked at from a specific entrypoint. These models can be found under tests/resources/models.

The definition of 1 is seperated into domains mapping largely to the subcomponents of the mcp (tmc, sdp etc), each with
its own conftest defining specific fixtures and shared step functions.

There are two options for running tests:
1. Exit immediately at the first failed test
2. Continue with attempts at teardown after failure

To enable immediate exit you need to set EXIT_AT_FAIL to "true"

Refer to the `Confluence page on installation of SKALLOP for BDD tests <https://confluence.skatelescope.org/display/SE/Skallop+installation+for+BDD+tests>`_ in the meantime.