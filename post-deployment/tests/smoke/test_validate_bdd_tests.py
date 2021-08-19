import logging
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from ska_ser_skallop.scripts.bdd_helper_scripts.xtp_compare import (
    output_file_diff as is_file_different,
)


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
    mocked_args.basic_auth_token = os.environ.get("JIRA_AUTH", "")
    mocked_args.feature_file = ""
    mocked_args.username = ""
    mocked_args.password = ""
    mocked_args.verbose = False

    assert not is_file_different(
        mocked_args, mocked_args.directory
    ), "Some BBD file(s) is not valid"
