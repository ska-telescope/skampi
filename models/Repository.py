import subprocess


class Repository:

    def __init__(self, name, github=None, gitlab=None):
        self.name = name
        self.github = github
        self.gitlab = gitlab
        self.readme_exists = None

    def set_gitlab(self, gitlab):
        self.gitlab = gitlab

    def set_readme_exists(self):
        if subprocess.call(["./docstatus/check-readme.sh", self.gitlab.path]):
            self.readme_exists = True
