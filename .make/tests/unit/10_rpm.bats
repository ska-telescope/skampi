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

@test 'RPM: correct package' {
    run make -f ../tests/Makefile rpm-package
    assert_success
}

@test 'RPM: no CMakeLists file' {
    mv CMakeLists.txt .CMakeLists.txt
    run make -f ../tests/Makefile rpm-package
    mv .CMakeLists.txt CMakeLists.txt
    assert_output -p "buildRpm: Missing CMakeLists.txt"
}