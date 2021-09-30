import logging
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from ska_ser_skallop.scripts.bdd_helper_scripts.xtp_compare import (
    file_differences,
    get_file_paths,
)

@pytest.mark.xfail
@pytest.mark.common
@pytest.mark.quarantine
def test_validate_bdd_features():
    """Make sure all the BDD feature files are in line with that in Jira"""

    test_file_path = Path(__file__)
    features_path = str(Path.joinpath(test_file_path.parents[2], "features").absolute())
    assert os.path.isdir(
        features_path
    ), f"Features path, {features_path} does not exist, test file path {test_file_path}"

    mocked_args = MagicMock()
    mocked_args.directory = features_path
    mocked_args.jira_auth_token = os.environ.get("JIRA_AUTH")
    mocked_args.feature_file = ""
    mocked_args.username = ""
    mocked_args.password = ""
    mocked_args.verbose = False

    feature_file_paths = get_file_paths(mocked_args.directory)
    assert not file_differences(
        mocked_args, feature_file_paths
    ), "The information in some of the local XTP files does not match with what is in Jira"
