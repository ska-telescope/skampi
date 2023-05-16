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

@test 'DOCS: check help' {
    run make -f ../tests/Makefile docs-help html
    echo "$output"
    assert_success
}

@test "DOCS: check docs build" {
    run make -f ../tests/Makefile DOCS_SOURCEDIR=../docs/src docs-build html
    echo "$output"
    assert_success
}
