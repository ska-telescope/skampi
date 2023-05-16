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


@test 'RELEASE: check .release file DOES NOT exists' {
  run bash -c "test -f ../build/.release"
  assert_failure
}

@test "RELEASE: Generate .release file" {
    run cd ../build && make -f ../tests/Makefile .release
    echo "$output"
    assert_success
}

@test 'RELEASE: check .release file exists' {
  run cd ../build && bash -c "test -f ../build/.release"
  assert_success

  # On failure, $status and $output are displayed.
  # -- command failed --
  # status : 23
  # output : Error!
  # --
}

@test 'RELEASE: check release is 0.0.0' {
  run grep -E 'release=0.0.0' ../build/.release
  assert_success
}

@test 'RELEASE: increment major release' {
  run  cd ../build && make -f ../tests/Makefile bump-major-release
  run grep -E 'release=1.0.0' ../build/.release
  assert_success
}

@test 'RELEASE: increment minor release - 1.1.0' {
  run  cd ../build && make -f ../tests/Makefile bump-minor-release
  run grep -E 'release=1.1.0' ../build/.release
  assert_success
}

@test 'RELEASE: increment patch release - 1.1.1' {
  run cd ../build && make -f ../tests/Makefile bump-patch-release
  run grep -E 'release=1.1.1' ../build/.release
  assert_success
}

@test 'RELEASE: increment major release using RELEASE_CONTEXT_DIR 0.0.0 -> 1.0.0' {
  run  cd ../build && make -f ../tests/Makefile bump-major-release RELEASE_CONTEXT_DIR=images/ska-cicd-makefile
  run grep -E 'release=1.0.0' ../build/images/ska-cicd-makefile/.release
  assert_success
}

@test 'RELEASE: increment major release using RELEASE_CONTEXT_DIR again 1.0.0 -> 2.0.0' {
  cat ../build/images/ska-cicd-makefile/.release
  echo "BEFORE"
  run  cd ../build && make -f ../tests/Makefile bump-major-release RELEASE_CONTEXT_DIR=images/ska-cicd-makefile
  echo "AFTER"
  run grep -E 'release=2.0.0' ../build/images/ska-cicd-makefile/.release
  cat ../build/images/ska-cicd-makefile/.release
  assert_success
}

@test 'RELEASE: check-status' {
  run make -f ../tests/Makefile check-status
  echo "After:"
  cat ../build/.release
  echo "$output"
  assert_success
}

@test 'RELEASE: dirty check-status' {
  echo "<--! making the release dirty -->" >> ../README.md
  run make -f ../tests/Makefile check-status
  assert_failure
  sed -i '$d' ../README.md
}


@test 'RELEASE: check generateTagReleaseNotes CHANGELOG.ska.md was created' {
  run bash -c "cd .. && . .make-release-support ; CHANGELOG_CONFIG=.chglog/config.yml CHANGELOG_TEMPLATE=.chglog/CHANGELOG.tpl.md generateTagReleaseNotes"
  echo "$output"
  run test -f ../CHANGELOG.ska.md
  echo "$output"
  assert_success
}

@test 'RELEASE: check getJiraTicketFromCommit Jira ticket successfully extracted' {
  run bash -c "cd .. && . .make-release-support ; CI_COMMIT_MESSAGE='ST-915: testing this' getJiraTicketFromCommit"
  assert_output -p "ST-915"
}

@test 'RELEASE: check getJiraTicketFromCommit No Jira ticket extracted' {
  run bash -c "cd .. && . .make-release-support ; CI_COMMIT_MESSAGE='ST:916: testing this' getJiraTicketFromCommit"
  assert_output -p ""
}

@test 'RELEASE: check extractAndInsertAuthorNotes.py saves author notes from CHANGELOG.md and adds them to the correct realeases in changelog.ska.md' {
  cat  ../tests/resources/changelog_test/CHANGELOG.ska.noNotes.md > ../tests/resources/changelog_test/CHANGELOG.ska.md
  python3 ../resources/extractAndInsertAuthorNotes.py ../tests/resources/changelog_test/CHANGELOG.md ../tests/resources/changelog_test/CHANGELOG.ska.md
  run diff ../tests/resources/changelog_test/CHANGELOG.ska.md ../tests/resources/changelog_test/CHANGELOG.expected.md
  rm ../tests/resources/changelog_test/CHANGELOG.ska.md
  assert_success
}
