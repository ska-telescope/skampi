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


@test "HELP: run help" {
    run make -f ../tests/Makefile
    echo "$output"
    [ $status -eq 0 ]
}

@test 'HELP: check help output contains ansible-lint|cpp-build|helm-lint|python-build|raw-publish-all|k8s-install-chart|submodule|oci-buildi-all|long-help|bump-major-release|rpm-package|bats-test|dev-vscode|conan-publish-all|docs-build - one from each mk file' {
  local -r log_txt="${BATS_TEST_TMPDIR}/log.txt"
  {
    make -f ../tests/Makefile
  } > "${log_txt}"
  run bash -c "grep -E 'ansible-lint|cpp-build|helm-lint|python-build|raw-publish-all|k8s-install-chart|submodule|oci-buildi-all|long-help|bump-major-release|rpm-package|bats-test|dev-vscode|conan-publish-all|docs-build'  ${log_txt} | wc -l | xargs"
  echo "Output: ${output}#"
  # Total makefiles + 1 as version update message could also appear
  [[ $output -ge 17 && $output -le 19 ]]
}
