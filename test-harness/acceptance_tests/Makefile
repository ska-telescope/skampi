############container makes######################################

build: cont_invoke ## build the base dependencies needed for basic operations
	pip3 install -r requirements

invoke:
	p=$$(pwd) ; \
	cd / ; \
	. /venv/bin/activate ; \
	cd $$p 

interactive:
	. /venv/bin/itango3 --profile=ska

test: cont_build ## run tests
	py.test

	




