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

@test 'OCI: check good Dockerfile' {
    run make -f ../tests/Makefile oci-lint
    echo "$output"
    assert_success
}

@test "OCI: check bad Dockerfile" {
    run make -f ../tests/Makefile oci-lint OCI_IMAGE_FILE_PATH=Dockerfile.bad
    echo "$output"
    assert_failure
}

@test 'OCI: build good Dockerfile' {
    cp ../tests/Makefile ../build/Makefile
    run make -f ../tests/Makefile oci-build-all CAR_OCI_REGISTRY_HOST=registry.gitlab.com/ska-telescope/sdi/ska-cicd-makefile OCI_SKIP_PUSH=yes
    echo "$output"
    assert_success
}

@test 'OCI: rebuild good Dockerfile with RELEASE_CONTEXT_DIR=images/ska-cicd-makefile' {
    cp ../tests/Makefile ../build/Makefile
    run make -f ../tests/Makefile oci-build CAR_OCI_REGISTRY_HOST=registry.gitlab.com/ska-telescope/sdi/ska-cicd-makefile OCI_SKIP_PUSH=yes RELEASE_CONTEXT_DIR=images/ska-cicd-makefile OCI_IMAGE=ska-cicd-makefile
    echo "$output"
    assert_success
}

@test 'OCI: check metadata with spaces in it' {
    cp ../tests/Makefile ../build/Makefile
    local oci_builder="docker"
    local image_name="ska-cicd-makefile"
    local version="0.0.0"
    export GITLAB_USER_NAME="Ugur Yilmaz <ugur.yilmaz@skao.int>"
    echo "Using GITLAB_USER_NAME with value: " $GITLAB_USER_NAME
    run make -f ../tests/Makefile oci-build OCI_IMAGE=$image_name VERSION=$version OCI_SKIP_PUSH=yes 
    echo "$output"
    assert_success
    run $oci_builder inspect $image_name:$version
    echo "$output"
    run $oci_builder inspect $image_name:$version -f {{.Config.Labels.GITLAB_USER_NAME}}
    echo "$output"
    assert_equal "$output" "$GITLAB_USER_NAME"
}


@test 'OCI: check metadata with spaces and quotes in it' {
    cp ../tests/Makefile ../build/Makefile
    local oci_builder="docker"
    local image_name="ska-cicd-makefile"
    local version="0.0.0"
    export GITLAB_USER_NAME="\"Ugur Yilmaz\" \"<ugur.yilmaz@skao.int>\""
    echo "Using GITLAB_USER_NAME with value: " $GITLAB_USER_NAME
    run make -f ../tests/Makefile oci-build OCI_IMAGE=$image_name VERSION=$version OCI_SKIP_PUSH=yes 
    echo "$output"
    assert_success
    run $oci_builder inspect $image_name:$version
    echo "$output"
    run $oci_builder inspect $image_name:$version -f {{.Config.Labels.GITLAB_USER_NAME}}
    echo "$output"
    assert_equal "$output" "$GITLAB_USER_NAME"
}

@test 'OCI: scan an image' {
    local trivy_image=${SKA_TRIVY_IMAGE}
    if [ -z $trivy_image ]; then
        echo "OCI: Could not find SKA_TRIVY_IMAGE env var"
        local trivy_image="docker.io/aquasec/trivy:0.24.4"
        echo "OCI: setting trivy image as $trivy_image"
        trivy () (docker run --rm -e TRIVY_NO_PROGRESS="true" docker.io/aquasec/trivy:0.24.4 $@)
    else
        trivy () (docker run --rm -e TRIVY_NO_PROGRESS="true" $SKA_TRIVY_IMAGE $@)
    fi
    echo "OCI: Downloading trivy image $trivy_image"
    run docker pull $trivy_image
    assert_success
    echo "OCI: Testing oci-scan using $trivy_image image"
    # Override trivy image with docker equvalent
    export -f trivy
    # The scan command uses the trivy image and mounts the $(CURDIR) to call Makefile targets
    # As trivy image doesn't have make and bash, we need to install it
    # TRIVY_NO_PROGRESS and TRIVY_CACHE_DIR is defined to match the CI/CD templates
    run make -f ../tests/Makefile oci-scan CAR_OCI_REGISTRY_HOST="docker.io" OCI_IMAGE=alpine VERSION=3.14
    echo "$output"
    assert_success
}

@test 'OCI: build with additional dev tags' {
    cp ../tests/Makefile ../build/Makefile
    local oci_builder="docker"
    local image_name="ska-cicd-makefile"
    local image_registry="registry.gitlab.com/ska-telescope/sdi/ska-cicd-makefile"
    local version="0.0.0"
    local commit_sha="abcd1234"
    local dev_tag_1=$commit_sha
    local dev_tag_2="foobar"

    run make -f ../tests/Makefile oci-build OCI_IMAGE=$image_name CAR_OCI_REGISTRY_HOST=$image_registry VERSION=$version OCI_SKIP_PUSH=yes OCI_BUILD_ADDITIONAL_TAGS="$dev_tag_1 $dev_tag_2" CI_COMMIT_SHORT_SHA=$commit_sha
    echo "$output"

    run $oci_builder inspect $image_registry/$image_name:$version-dev.c$commit_sha
    assert_success
    run $oci_builder inspect $image_registry/$image_name:$dev_tag_1
    assert_success
    run $oci_builder inspect $image_registry/$image_name:$dev_tag_2
    assert_success
}
