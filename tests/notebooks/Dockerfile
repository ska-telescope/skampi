FROM registry.gitlab.com/ska-telescope/ska-skampi/ska-skampi-ci-base:0.1.0

COPY . ./

RUN python3 -m pip install --no-cache-dir notebook jupyterlab

RUN pip install --no-cache-dir -r requirements.txt
