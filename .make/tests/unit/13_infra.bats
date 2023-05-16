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

@test 'INFRA: make orch - fail' {
    run make -f ../tests/Makefile orch
    assert_failure
}

@test 'INFRA: make orch' {
    run make -f ../tests/Makefile orch DATACENTRE=d ENVIRONMENT=e SERVICE=s TF_HTTP_USERNAME=u TF_HTTP_PASSWORD=p
    assert_success
}

@test 'INFRA: make playbooks - fail' {
    run make -f ../tests/Makefile playbooks
    assert_failure
}

@test 'INFRA: make playbooks' {
    run make -f ../tests/Makefile playbooks DATACENTRE=d ENVIRONMENT=e SERVICE=s
    assert_success
}
