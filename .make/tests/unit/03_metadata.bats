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


@test 'METADATA: run metadataGenerate without args - fails' {
  run bash -c ". ../.make-metadata-support ; metadataGenerate"
  echo "$output"
  assert_failure
}

@test 'METADATA: run metadataGenerate with MANIFEST.skao.int' {
  run bash -c ". ../.make-metadata-support ; metadataGenerate MANIFEST.skao.int"
  echo "$output"
  assert_success
}

@test 'METADATA: check VERSION in MANIFEST.skao.int (1.1.1)' {
  run grep 'VERSION=1.1.1' MANIFEST.skao.int
  echo "$output"
  assert_success
}
