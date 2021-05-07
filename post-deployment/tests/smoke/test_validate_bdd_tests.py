import logging
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from skallop.scripts.bdd_helper_scripts.xtp_compare import (
    check_local_file,
    parse_local_feature_files,
)


@pytest.mark.skamid
@pytest.mark.xfail
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


    parsed_local_files = parse_local_feature_files(mocked_args)
    assert parsed_local_files, "No parsed feature files."
    found_issues = []
    for local_file in parsed_local_files:
        logging.info("Checking file %s", local_file.file_path)
        issues = check_local_file(mocked_args, local_file)
        for issue in issues:
            logging.info(issue)
        found_issues.extend(issues)
    assert not found_issues, "Some BDD files not valid"
