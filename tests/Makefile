# Use bash shell with pipefail option enabled so that the return status of a
# piped command is the value of the last (rightmost) commnand to exit with a
# non-zero status. This lets us pipe output into tee but still exit on test
# failures.
EXIT_AT_FAIL ?=false## set python test to exit at the first failed test
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

all: test

.PHONY: all test install start_log_consumer remove_log_consumer setup_ipython config_git check_running get_mem_usage get_cpu_usage

ifneq ($(EXIT_AT_FAIL),false)
EXIT = -x
else
EXIT = 
endif

test: install
	# make start_log_consumer # does not start:
	# omniORB: (0) 2021-10-13 14:29:20.153601: Error: cannot create directory: /tmp/omni-root
	# omniORB: (0) 2021-10-13 14:29:20.153613: Error: Unable to create an endpoint of this description: giop:unix:
	# make remove_log_consumer
	echo "KUBE_NAMESPACE: $${KUBE_NAMESPACE}"
	mkdir -p build && \
	find . -name "*.pyc" -type f -delete && \
	cd .. && \
	pytest --version; \
	PYTHONPATH=/app:/app/skampi:/app/skampi/test KUBE_NAMESPACE=$(KUBE_NAMESPACE) pytest -v -r fEx \
		$(if $(findstring all,$(MARK)),, -m '$(MARK)') \
		--disable-pytest-warnings $(FILE) --count=$(COUNT) --repeat-scope session tests $(EXIT)| tee pytest.stdout; \
	status=$$?; \
	echo "test: status is ($$status)"; \
	cp -r ./build/* tests/build/; \
	exit $$status

install:
	if [[ -f test_requirements.txt ]]; then pip3 install -r test_requirements.txt -qq; fi

start_log_consumer:
	tango_admin --add-server LogConsumer/log LogConsumer LogConsumer/log/log01 && \
	(python3 resources/log_consumer/log_consumer.py log &)

remove_log_consumer:
	kill $$(ps aux | grep -v grep | grep 'python3 resources/log_consumer/log_consumer.py' | awk '{print $$2}') && \
	 (tango_admin --delete-server log_consumer/log &)

setup_ipython:
	ipython profile create &&  \
	cp resources/ipython_config.py /home/tango/.ipython/profile_default/ipython_config.py

check_running:
	ps aux

get_mem_usage:
	@raw=$$(cat /sys/fs/cgroup/memory/memory.usage_in_bytes) && \
	mb=$$(expr 1024 \* 1024) && \
	MB=$$(expr $$raw / $$mb) && \
	echo "$$MB"MB

get_cpu_usage:
	@raw=$$(cat /sys/fs/cgroup/cpu/cpu.shares ) && \
	echo $$raw
	