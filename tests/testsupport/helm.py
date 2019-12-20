import subprocess


class HelmTestAdaptor(object):
    HELM_TEMPLATE_CMD = "helm template --name {} -x templates/{} charts/{}"
    HELM_DELETE_CMD = "helm delete {} --purge"
    HELM_INSTALL_CMD = "helm install charts/{} --namespace ci --wait"

    def __init__(self, chart_name, use_tiller_plugin):
        self.chart_name = chart_name
        self.use_tiller_plugin = use_tiller_plugin

    def deploy_chart(self):
        cmd_stdout = self.run_cmd(self.HELM_INSTALL_CMD.format(self.chart_name))
        return self._parse_helm_release_name_from(cmd_stdout)

    def undeploy_chart(self, helm_release):
        self.run_cmd(self.HELM_DELETE_CMD.format(helm_release))

    def render_template(self, release_name, template):
        return self.run_cmd(HelmTestAdaptor.HELM_TEMPLATE_CMD.format(release_name, template, self.chart_name))

    def _parse_helm_release_name_from(self, stdout):
        release_name_line = ''.join(l for l in stdout.split('\n') if l.startswith('NAME:'))
        release_name = release_name_line.split().pop()
        return release_name

    def run_cmd(self, helm_cmd):
        if self.use_tiller_plugin is True:
            deploy_cmd = self.prefix_cmd_with_tiller_run(helm_cmd)
        else:
            deploy_cmd = helm_cmd.split()
        cmd_stdout = self._run_subprocess(deploy_cmd)
        return cmd_stdout

    @staticmethod
    def _run_subprocess(shell_cmd):
        result = subprocess.run(shell_cmd, stdout=subprocess.PIPE, encoding="utf8", check=True)
        return result.stdout

    @staticmethod
    def prefix_cmd_with_tiller_run(helm_cmd):
        HELM_TILLER_PREFIX = "helm tiller run -- "
        deploy_cmd = (HELM_TILLER_PREFIX + helm_cmd).split()
        return deploy_cmd