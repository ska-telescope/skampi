############container makes######################################

build: invoke ## build the base dependencies needed for basic operations
	pip3 install -r requirements

invoke:
	. /venv/bin/activate ;

interactive:
	. /venv/bin/itango3 --profile=ska

test: build ## run tests
	py.test | tee setup_py_test.stdout; \
	status=$$?; \
	exit $$status

	




