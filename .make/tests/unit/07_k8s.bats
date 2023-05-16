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

@test 'K8S: get chart version' {
    run make -f ../tests/Makefile k8s-chart-version K8S_CHART=ska-tango-base K8S_HELM_REPOSITORY=https://artefact.skao.int/repository/helm-internal/
    echo "Version: $output"
    echo "$output" > ../build/k8s-chart-version.txt
    run grep -E '[0-9]+\.[0-9]+\.[0-9]+' ../build/k8s-chart-version.txt
    cat ../build/k8s-chart-version.txt
    assert_success
}
