import json
import logging

import pytest

from resources.test_support.helm import ChartDeployment, HelmChart


@pytest.fixture(scope="class")
def skuid_chart(request, helm_adaptor):
    chart_values = {
        'ingress.enabled': 'true'
    }
    request.cls.chart = HelmChart("skuid", helm_adaptor, initial_chart_values=chart_values)


@pytest.fixture(scope="class")
def skuid_chart_deployment(helm_adaptor, k8s_api):
    logging.info("+++ Deploying skuid chart.")
    chart_deployment = ChartDeployment("skuid", helm_adaptor, k8s_api)
    yield chart_deployment
    logging.info("+++ Deleting skuid chart release.")
    chart_deployment.delete()


@pytest.mark.no_deploy
@pytest.mark.usefixtures("skuid_chart")
class TestSkuidChart:
    def test_skuid_image_name_and_version(self):
        d = self.chart.templates["skuid.yaml"].as_objectpath()
        image_name = d.execute("$..*.image[0]")

        assert image_name == "nexus.engageska-portugal.pt/ska-telescope/skuid:1.1.0"

    def test_env_vars_loaded_from_skuid_config_map(self):
        d = self.chart.templates["skuid.yaml"].as_objectpath()
        configmap_name = self.chart.templates["skuid-cm.yaml"].as_collection()[0]['metadata']['name']

        configmapref = d.execute("$..*.configMapRef[0]")
        assert configmapref['name'] == configmap_name

    def test_pv_mount_path_should_be_same_as_data_dir(self):
        data_dir = '/data-test'
        chart = self.chart.render_template('skuid.yaml', chart_values={ 
            'ingress.enabled': 'true',
            'skuid.config.data_dir': data_dir
        })

        d = chart.as_objectpath()

        volume_mount = d.execute(f"$..volumeMounts.*[@.name is 'skuid-data'][0]")

        assert volume_mount['mountPath'] == data_dir

    def test_config_mount_path_should_be_same_as_config_dir(self, helm_adaptor):
        config_path = '/etc/skuid-test'
        chart = HelmChart("skuid", helm_adaptor, initial_chart_values={
            'ingress.enabled': 'true',
            'skuid.config.entity_types.override': 'true',
            'skuid.config.config_dir': config_path
        })

        d = chart.templates["skuid.yaml"].as_objectpath()
        volume_mount = d.execute("$..*.volumeMounts..*[@.name is 'skuid-config'][0]")

        assert volume_mount['mountPath'] == config_path

    def test_charts(self, skuid_chart):
        ingress_chart = self.chart.templates["skuid-ingress.yaml"].as_collection()[0]
        assert (
            ingress_chart["spec"]["rules"][0]["host"]
            == "integration.engageska-portugal.pt"
        )
        assert (
            ingress_chart["spec"]["rules"][0]["http"]["paths"][0]["backend"][
                "servicePort"
            ]
            == 9870
        )

        pv_chart = self.chart.templates["skuid-pv.yaml"].as_collection()
        skuid_pvc = list(
            filter(lambda x: x["kind"] == "PersistentVolumeClaim", pv_chart)
        )[0]
        if (skuid_pvc["spec"]["storageClassName"] == "standard"):
            skuid_pv = list(filter(lambda x: x["kind"] == "PersistentVolume", pv_chart))[0]
            
            assert skuid_pv["spec"]["persistentVolumeReclaimPolicy"] == "Recycle"
            assert skuid_pv["spec"]["capacity"]["storage"] == "100Mi"
            assert skuid_pv["spec"]["accessModes"] == ["ReadWriteOnce"]

            assert skuid_pvc["spec"]["accessModes"] == ["ReadWriteOnce"]
            assert skuid_pvc["spec"]["resources"]["requests"]["storage"] == "100Mi"

        squid_chart = self.chart.templates["skuid.yaml"].as_collection()
        squid_deployment = list(
            filter(lambda x: x["kind"] == "Deployment", squid_chart)
        )[0]
        squid_service = list(filter(lambda x: x["kind"] == "Service", squid_chart))[0]

        containers_spec = squid_deployment["spec"]["template"]["spec"]["containers"][0]
        assert containers_spec["ports"][0]["name"] == "skuid-http"
        assert containers_spec["ports"][0]["containerPort"] == 9870
        assert containers_spec["volumeMounts"][0]["name"] == "skuid-data"

        assert squid_service["spec"]["type"] == "ClusterIP"
        assert squid_service["spec"]["ports"][0]["port"] == 9870
        assert squid_service["spec"]["ports"][0]["targetPort"] == 9870


@pytest.mark.chart_deploy
@pytest.mark.usefixtures("skuid_chart_deployment")
class TestSkuidDeployment:
    def test_skuid_is_up_and_serving(self, skuid_chart_deployment):
        """Check that skuid is up and base path is as expected"""
        skuid_pod_name = skuid_chart_deployment.search_pod_name("skuid-deployment")[0]

        command_str = "curl -s  -X GET http://0.0.0.0:9870/"
        resp = skuid_chart_deployment.pod_exec_bash(skuid_pod_name, command_str)
        assert "Welcome to skuid" in resp

        command_str = "curl -s  -X GET http://0.0.0.0:9870/skuid"
        resp = skuid_chart_deployment.pod_exec_bash(skuid_pod_name, command_str)
        assert "Welcome to skuid" in resp

        command_str = "curl -s  -X GET http://0.0.0.0:9870/skuid/ska_id/test"
        resp = skuid_chart_deployment.pod_exec_bash(skuid_pod_name, command_str)
        resp_json = json.loads(resp)
        resp_json = json.loads(resp_json)
        assert "ska_uid" in resp_json
        assert "generator_id" in resp_json
        assert resp_json["generator_id"] == "T0001"

        command_str = "curl -s  -X GET http://0.0.0.0:9870/skuid/ska_scan_id"
        resp = skuid_chart_deployment.pod_exec_bash(skuid_pod_name, command_str)
        resp_json = json.loads(resp)
        resp_json = json.loads(resp_json)

        command_str = "curl -s  -X GET http://0.0.0.0:9870/skuid/entity_types/get"
        resp = skuid_chart_deployment.pod_exec_bash(skuid_pod_name, command_str)
        resp_json = json.loads(resp)
        resp_json = json.loads(resp_json)
        assert len(resp_json) > 5

    def test_skuid_response_time(self, skuid_chart_deployment):
        """Ensure the response times are less than 1/20 of a second.
        NOTE: These timings do not take k8s networking overhead into account
        """
        skuid_pod_name = skuid_chart_deployment.search_pod_name("skuid-deployment")[0]

        command_str = (
            "curl -X GET -L --output /dev/null  --silent --write-out"
            " '%{time_total}' http://0.0.0.0:9870/"
        )
        for path in [
            "",
            "skuid",
            "skuid/ska_id/test",
            "skuid/ska_scan_id",
            "skuid/entity_types/get"
        ]:
            resp = skuid_chart_deployment.pod_exec_bash(
                skuid_pod_name, command_str + path
            )
            logging.info(f"Time for path {path}: {resp}")
            resp = float(resp)
            assert resp < 0.05
