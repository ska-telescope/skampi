.PHONY: template_tests


template_tests:
	rc=0; \
	for chrt in `ls charts/`; do \
	helm unittest -f template_tests/*_test.yaml charts/$$chrt \
		|| rc=2 && continue; \
	done; \
	exit $$rc

template_pytests:
	pytest -m no_deploy $(if $(CI),,--use-tiller-plugin)

chart_pytests:
	pytest -m chart_deploy $(if $(CI),,--use-tiller-plugin)