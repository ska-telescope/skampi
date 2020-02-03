# Use bash shell with pipefail option enabled so that the return status of a
# piped command is the value of the last (rightmost) commnand to exit with a
# non-zero status. This lets us pipe output into tee but still exit on test
# failures.
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

TEST_ARTIFACTS = setup_py_test.stdout report.xml report.json cucumber.json pytest-logs.txt

all: test

# create the build directory
# execute the python tests
# copy TEST_ARTIFACTS into build directory
# exit with same exit code as test run
test:
	@mkdir -p build
	python setup.py test | tee setup_py_test.stdout; \
		status=$$?; \
		$(foreach artfct,$(TEST_ARTIFACTS),mv -f $(artfct) build/;) \
		exit $$status

.PHONY: all test

install:
	pip3 install -r test_requirements.txt

pytest:
	py.test


