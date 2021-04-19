# import requests
import pytest
# import os
# from assertpy import assert_that

@pytest.mark.quarantine
@pytest.mark.skamid
@pytest.mark.skalow
def test_quarantined_test_is_executed():
    # this test should always pass and is just a waste of resources
    pass


@pytest.mark.common
def test_quarantined_tests_fail_and_pipeline_succeeds():
    # This test should fail and pipeline should remain orange
    assert False