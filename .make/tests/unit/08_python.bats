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

@test 'PYTHON: package with metadata for tag_setup' {
    run make -f ../tests/Makefile python-build PYTHON_BUILD_TYPE=tag_setup
    echo "$output"
    assert_success
}

@test 'PYTHON: package with metadata for non_tag_setup' {
    run make -f ../tests/Makefile python-build PYTHON_BUILD_TYPE=non_tag_setup
    echo "$output"
    assert_success
}

@test 'PYTHON: package with metadata for tag_pyproject' {
    cp -f pyproject.toml.default pyproject.toml
    run make -f ../tests/Makefile python-build PYTHON_BUILD_TYPE=tag_pyproject
    echo "$output"
    assert_success
}

@test 'PYTHON: package with metadata for non_tag_pyproject' {
    cp -f pyproject.toml.default pyproject.toml
    run make -f ../tests/Makefile python-build PYTHON_BUILD_TYPE=non_tag_pyproject
    echo "$output"
    assert_success
}

@test 'PYTHON: package with metadata for tag_pyproject and altsrc' {
    pwd
    cp -f pyproject.toml.altsrc pyproject.toml
    run make -f ../tests/Makefile python-build PYTHON_BUILD_TYPE=tag_pyproject PYTHON_SRC=altsrc
    echo "$output"
    assert_success
}

@test 'PYTHON: package with metadata for tag_pyproject and badsrc' {
    pwd
    cp -f pyproject.toml.badsrc pyproject.toml
    rm -rf ./dist
    run make -f ../tests/Makefile python-build PYTHON_BUILD_TYPE=tag_pyproject PYTHON_SRC=badsrc
    echo "$output"
    assert_failure
}

@test 'Python: gemnasium scanning' {
    local analyser=${SKA_GEMNASIUM_IMAGE}
    if [ -z $analyser ]; then
        echo "Python: Could not find SKA_GEMNASIUM_IMAGE env var"
        local analyser="registry.gitlab.com/ska-telescope/ska-cicd-k8s-tools/ska-cicd-gemnasium-scanning-alpine:0.7.1"
        echo "Python: setting analyser image as $analyser"
        analyser () (docker run --rm -e  registry.gitlab.com/ska-telescope/ska-cicd-k8s-tools/ska-cicd-gemnasium-scanning-alpine:0.7.1 $@)
    else
        analyser () (docker run --rm -e  $SKA_GEMNASIUM_IMAGE $@)
    fi
    echo "Python: Downloading gemnasium image $analyser"
    run docker pull $analyser
    assert_success
    echo "Python: Testing python-scan using $analyser image"
    # Override analyser image with docker equvalent
    export -f analyser
    # The scan command uses the analyser image and mounts the $(CURDIR) to call Makefile targets
    run make -f ../tests/Makefile python-scan PYTHON_BUILD_TYPE=tag_pyproject
    echo "$output"
    assert_success
}

