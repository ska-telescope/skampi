.PHONY: template_tests

CHART_TESTING_TOOL = https://github.com/helm/chart-testing/releases/download/v2.4.0/chart-testing_2.4.0_linux_amd64.tar.gz

template_tests:
	rc=0; \
	for chrt in `ls charts/`; do \
	helm unittest -f template_tests/*_test.yaml charts/$$chrt \
		|| rc=2 && continue; \
	done; \
	exit $$rc
