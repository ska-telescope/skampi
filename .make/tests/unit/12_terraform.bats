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

@test 'TERRAFORM: Valid against cpp src directory' {
    run make -f ../tests/Makefile TERRAFORM_LINT_TARGET=./src tf-lint
    assert_success
}

@test 'TERRAFORM: Valid against docker src directory' {
    run make -f ../tests/Makefile TERRAFORM_LINT_TARGET=./images/ska-cicd-makefile tf-lint
    assert_success
}

@test 'TERRAFORM: Valid against conan src directory' {
    run make -f ../tests/Makefile TERRAFORM_LINT_TARGET=./conan tf-lint
    assert_success
}

@test 'TERRAFORM: Valid format check' {
    run bash -c ". ../.make-terraform-support; \
    TERRAFORM_RUNNER=terraform \
    TERRAFORM_LINT_TARGET_ID=tf-good-module terraformCheckFormat ./terraform/tf-good-module"
    assert_success
}

@test 'TERRAFORM: Wrong format check' {
    run bash -c ". ../.make-terraform-support; \
    TERRAFORM_RUNNER=terraform \
    TERRAFORM_LINT_TARGET_ID=tf-bad-format terraformCheckFormat ./terraform/tf-bad-format"
    assert_failure
}

@test 'TERRAFORM: Valid code' {
    run bash -c ". ../.make-terraform-support; \
    TERRAFORM_RUNNER=terraform \
    TERRAFORM_LINT_TARGET_ID=tf-good-module terraformValidate ./terraform/tf-good-module"
    assert_success
}

@test 'TERRAFORM: Invalid type passed' {
    run bash -c ". ../.make-terraform-support; \
    TERRAFORM_RUNNER=terraform \
    TERRAFORM_LINT_TARGET_ID=tf-bad-type terraformValidate ./terraform/tf-bad-type"
    assert_failure
}

@test 'TERRAFORM: Linted code' {
    run bash -c ". ../.make-terraform-support; \
    TERRAFORM_RUNNER=terraform \
    TERRAFORM_TFLINT_RUNNER=tflint \
    TERRAFORM_LINT_TARGET_ID=tf-good-module terraformLint ./terraform/tf-good-module"
    assert_success
}

@test 'TERRAFORM: Unspecified terraform version' {
    run bash -c ". ../.make-terraform-support; \
    TERRAFORM_RUNNER=terraform \
    TERRAFORM_TFLINT_RUNNER=tflint \
    TERRAFORM_LINT_TARGET_ID=tf-unspecified-version terraformLint ./terraform/tf-unspecified-version"
    assert_failure
}

@test 'TERRAFORM: Wrong module' {
    run make -f ../tests/Makefile TERRAFORM_LINT_TARGET=./terraform/tf-unspecified-version tf-lint
    assert_failure
}

@test 'TERRAFORM: Valid module' {
    run make -f ../tests/Makefile TERRAFORM_LINT_TARGET=./terraform/tf-good-module tf-lint
    assert_success
}
