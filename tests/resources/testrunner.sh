#!/bin/bash -o pipefail -c

# The execution flow for the Skampi test-runner Job
cd /app

# install packages if required
if [[ -f pyproject.toml ]]; then
  poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes --dev
  echo 'k8s-test: installing poetry-requirements.txt'
  pip install -qUr poetry-requirements.txt
else
  if [[ -f ${K8S_TEST_FOLDER}/requirements.txt ]]; then
    echo 'k8s-test: installing ${K8S_TEST_FOLDER}/requirements.txt'
    pip install -qUr ${K8S_TEST_FOLDER}/requirements.txt
  fi
fi

# setup proxy values
if [ -n "${PSI_LOW_PROXY_VALUES}" ]; then
  export ${PSI_LOW_PROXY_VALUES}
fi

# setup the environment
cd ${K8S_TEST_FOLDER}
export PYTHONPATH=${PYTHONPATH}:/app/src${K8S_TEST_SRC_DIRS}
mkdir -p build

# take the Makefile from the ConfigMap
cp /config/Makefile /app/tests/Makefile

echo "The complete environment is:"
printenv
echo ""; echo ""

# run the Make test target
make -s \
			${K8S_TEST_MAKE_PARAMS} \
			${K8S_TEST_TARGET}

# capture the test result
echo $? > build/status
pip list > build/pip_list.txt

# put the results on the PersistentVolumeClaim
cp -r /build/* /data/
echo "k8s_test_command: test command exit is: $(cat build/status)"

exit 0
