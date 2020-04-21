# Use bash shell with pipefail option enabled so that the return status of a
# piped command is the value of the last (rightmost) commnand to exit with a
# non-zero status. This lets us pipe output into tee but still exit on test
# failures.
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

TEST_ARTIFACTS = report.xml report.json cucumber.json pytest-logs.txt

all: test

# create the build directory
# execute the python tests
# copy TEST_ARTIFACTS into build directory
# exit with same exit code as test run
test: install
	tango_admin --add-server log_consumer/log log_consumer log_consumer/log/log01 && \
	(python3 resources/log_consumer/log_consumer.py log &); \
	mkdir -p build && \
	find . -name "*.pyc" -type f -delete && \
	if [ "$(MARK)" == "all" ]; then \
		PYTHONPATH=/app:/app/skampi:/app/skampi/post-deployment pytest --disable-pytest-warnings | tee pytest.stdout && status=$$?; \
	else \
		PYTHONPATH=/app:/app/skampi:/app/skampi/post-deployment pytest -m $(MARK) --disable-pytest-warnings | tee pytest.stdout && status=$$?; \
	fi; \
	(tango_admin --delete-server log_consumer/log &) && \
	$(foreach artfct,$(TEST_ARTIFACTS),mv -f $(artfct) build/;) \
	exit $$status

.PHONY: all test install

install:
	pip3 install -r test_requirements.txt
