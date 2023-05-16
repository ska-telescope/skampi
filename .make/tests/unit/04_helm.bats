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


@test 'HELM: check good chart' {
    mkdir -p charts
    helm create charts/good
    run make -f ../tests/Makefile helm-lint HELM_CHARTS=good
    echo "$output"
    assert_success
}

@test "HELM: check bad chart" {
    mkdir -p charts
    helm create charts/bad
    rm -rf charts/bad/Chart.yaml
    run make -f ../tests/Makefile helm-lint HELM_CHARTS=bad
    echo "$output"
    assert_failure
}

@test 'HELM: set chart release' {
    echo "####### Before:"
    cat ../build/charts/good/Chart.yaml
    run make -f ../tests/Makefile helm-set-release HELM_CHARTS="good bad"
    echo "$output"
    run grep -E 'version: 1.1.1' ../build/charts/good/Chart.yaml
    echo "####### After:"
    cat ../build/charts/good/Chart.yaml
    assert_success
}

@test 'HELM: do helm-build (no push)' {
    echo "####### Before:"
    cat ../build/charts/good/Chart.yaml
    run make -f ../tests/Makefile helm-build HELM_CHARTS_TO_PUBLISH=good RELEASE_CONTEXT_DIR=../ CI_PROJECT_ID=29572088 CI_JOB_TOKEN=test HELM_BUILD_PUSH_SKIP=yes
    echo "$output"
    assert_success
}
