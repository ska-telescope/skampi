# Use bash shell with pipefail option enabled so that the return status of a
# piped command is the value of the last (rightmost) commnand to exit with a
# non-zero status. This lets us pipe output into tee but still exit on test
# failures.
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

TEST_ARTIFACTS = pytest.stdout report.xml report.json cucumber.json pytest-logs.txt

all: test

# create the build directory
# execute the python tests
# copy TEST_ARTIFACTS into build directory
# exit with same exit code as test run
test:install
	@mkdir -p build && \
	find . -name "*.pyc" -type f -delete && \
	PYTHONPATH=/app:/app/skampi:/app/skampi/post-deployment pytest | tee pytest.stdout && \
		status=$$? && \
		$(foreach artfct,$(TEST_ARTIFACTS),mv -f $(artfct) build/;) \
		exit $$status

.PHONY: all test

install:
	pip3 install -r test_requirements.txt




