import subprocess


class HelmTestAdaptor(object):
    HELM_TEMPLATE_CMD = "helm template --namespace {} --name {} -x templates/{} charts/{}"
    HELM_DELETE_CMD = "helm delete {} --purge"
    HELM_INSTALL_CMD = "helm install charts/{} --namespace {} --wait"

    def __init__(self, use_tiller_plugin, test_namespace):
        self.use_tiller_plugin = use_tiller_plugin
        self.namespace = test_namespace

    def install(self, chart):
        cmd = self._wrap_tiller(self.HELM_INSTALL_CMD.format(chart, self.namespace))
        return self._run_subprocess(cmd.split())

    def delete(self, helm_release):
        cmd = self._wrap_tiller(self.HELM_DELETE_CMD.format(helm_release))
        return self._run_subprocess(cmd.split())

    def template(self, chart_name, release_name, template):
        cmd = self.HELM_TEMPLATE_CMD.format(self.namespace, release_name, template, chart_name)
        return self._run_subprocess(cmd.split())

    def _wrap_tiller(self, helm_cmd):
        if self.use_tiller_plugin is True:
            cli_cmd = self.__prefix_cmd_with_tiller_run(helm_cmd)
        else:
            cli_cmd = helm_cmd

        return cli_cmd

    @staticmethod
    def _run_subprocess(shell_cmd):
        result = subprocess.run(shell_cmd, stdout=subprocess.PIPE, encoding="utf8", check=True)
        return result.stdout

    @staticmethod
    def __prefix_cmd_with_tiller_run(helm_cmd):
        HELM_TILLER_PREFIX = "helm tiller run -- "
        deploy_cmd = (HELM_TILLER_PREFIX + helm_cmd)
        return deploy_cmd


class ChartDeployment(object):
    def __init__(self, chart, helm_adaptor):
        self.__helm_adaptor = helm_adaptor

        try:
            stdout = self.__helm_adaptor.install(chart)

            self.chart_name = chart
            self.release_name = self._parse_release_name_from(stdout)
        except Exception as e:
            raise RuntimeError('!!! Failed to deploy helm chart.', e)

    def delete(self):
        assert self.release_name is not None
        self.__helm_adaptor.delete(self.release_name)

    @staticmethod
    def _parse_release_name_from(stdout):
        release_name_line = ''.join(l for l in stdout.split('\n') if l.startswith('NAME:'))
        return release_name_line.split().pop()
