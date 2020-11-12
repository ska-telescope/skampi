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
test: install
	tango_admin --add-server LogConsumer/log LogConsumer LogConsumer/log/log01 && \
	(python3 resources/log_consumer/log_consumer.py log &); \
	mkdir -p build && \
	find . -name "*.pyc" -type f -delete && \
	PYTHONPATH=/app:/app/skampi:/app/skampi/post-deployment pytest $(if $(findstring all,$(MARK)),, -m $(MARK)) --disable-pytest-warnings | tee pytest.stdout; \
	status=$$?; \
	(tango_admin --delete-server log_consumer/log &) && \
	$(foreach artfct,$(TEST_ARTIFACTS),mv -f $(artfct) build/ || true;) \
	exit $$status

.PHONY: all test install

TEST_RUN_SPEC = example.yaml

test_multiple_runs: install
	tango_admin --add-server LogConsumer/log LogConsumer LogConsumer/log/log01 && \
	(python3 resources/log_consumer/log_consumer.py log &); \
	mkdir -p build && \
	find . -name "*.pyc" -type f -delete && \
	PYTHONPATH=/app:/app/skampi:/app/skampi/post-deployment python3 exploration/test_runs/run_it.py \
		-f exploration/test_runs/specs/$(TEST_RUN_SPEC) | tee pytest.stdout; \
	status=$$?; \
	(tango_admin --delete-server log_consumer/log &) && \
	$(foreach artfct,$(TEST_ARTIFACTS),mv -f $(artfct) build/;) \
	exit $$status


install:
	pip3 install -r test_requirements.txt

start_log_consumer:
	tango_admin --add-server LogConsumer/log LogConsumer LogConsumer/log/log01
	(python3 resources/log_consumer/log_consumer.py log &)

remove_log_consumer:
	kill $$(ps aux | grep -v grep | grep 'python3 resources/log_consumer/log_consumer.py' | awk '{print $$2}')
	tango_admin --delete-server LogConsumer/log

setup_ipython:
	ipython profile create &&  \
	cp resources/ipython_config.py /home/tango/.ipython/profile_default/ipython_config.py 

config_git:
	git config --global user.name '$(GIT_USER)'
	git config --global user.email $(GIT_EMAIL)

check_log_consumer_running:
	ps aux | awk 

set_auto_complete:
	echo 'source <(kubectl completion bash)' >>~/.bashrc

run_http:
	python3 exploration/web_pytest/web_pytest.py &

ping_http:
	curl http:30080//dev-testing/ping -v

export_extensions:
	cd ~ && \
	tar -cvzf vscode-server.tar .vscode-server && \
	mv vscode-server.tar ~/skampi/vscode-server.tar

get_mem_usage:
	@raw=$$(cat /sys/fs/cgroup/memory/memory.usage_in_bytes) && \
	mb=$$(expr 1024 \* 1024) && \
	MB=$$(expr $$raw / $$mb) && \
	echo "$$MB"MB

get_cpu_usage:
	@raw=$$(cat /sys/fs/cgroup/cpu/cpu.shares ) && \
	echo $$raw

SPEC=example.yaml
run_multiple:
	python3 exploration/test_runs/run_it.py -f exploration/test_runs/specs/$(SPEC)
