#!/usr/bin/env bats

# Load a library from the `${BATS_TEST_DIRNAME}/test_helper' directory.
#
# Globals:
#   none
# Arguments:
#   $1 - name of library to load
# Returns:
#   0 - on success
#   1 - otherwise
load_lib() {
  local name="$1"
  load "../../scripts/${name}/load"
}

load_lib bats-support
load_lib bats-assert

@test 'XRAY: test upload dry run' {
    run make -f ../tests/Makefile xray-publish \
      XRAY_EXTRA_OPTS='--dry-run' \
      XRAY_TEST_RESULT_FILE="xray/cucumber.json" \
      XRAY_EXECUTION_CONFIG_FILE="xray/xray-config.json"

    echo "$output"
    assert_success
}
