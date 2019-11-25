import subprocess
from github import Github
import gitlab


class Repository:

    def __init__(self, name, github=None, gitlab=None):
        self.name = name
        self.github = github
        self.gitlab = gitlab

    def set_gitlab(self, gitlab):
        self.gitlab = gitlab

    def set_readme_exists(self):
        if subprocess.call(["./docstatus/check-readme.sh", self.gitlab.path]):
            self.readme_exists = True


class GitHubRepo:
    def __init__(self, name):
        self.name = name
        self.mantainers = []
        self.teams = []

    def __str__(self):
        return "Name: " + str(self.name) + " || " + "Mantainers: " + str(self.mantainers)

    def add_maintainers(self, mantainers):
        for m in mantainers:
            if not m.login in self.mantainers:
                self.mantainers.append(m.login)

    def add_team(self, team):
        self.teams.append(team)


class GitLabRepo:
    def __init__(self, name, mirror, creator):
        self.name = name
        self.mirror = mirror
        self.creator = creator


def github_repositories():
    # using username and password
    g = Github("dfsn@ua.pt", "Slbbenfica94")  # put credentials here

    teams = g.get_organization("ska-telescope").get_teams()

    repos = {}
    for team in teams:
        for repo in team.get_repos():
            if repos.get(repo.name) == None:
                repos[repo.name] = GitHubRepo(repo.name)
                repos.get(repo.name).add_maintainers(team.get_members("maintainer"))
                repos.get(repo.name).add_team(team.name)
            else:
                repos.get(repo.name).add_maintainers(team.get_members("maintainer"))
                repos.get(repo.name).add_team(team.name)

    return repos


def list_gitlab_repositories():
    # private token or personal token authentication
    gl = gitlab.Gitlab('https://gitlab.com',
                       private_token='MX_2Q5yUqYvHWexVYaxu')  # get your token  here: https://gitlab.com/profile/personal_access_tokens

    group = gl.groups.get(3180705)

    projects = group.projects.list(all=True, order_by="name", sort="asc")

    result = []
    for project in projects:
        creator = gl.users.get(project.creator_id).username
        result.append(GitLabRepo(project.name, creator, project.path, project.mirror))

    return result


if __name__ == '__main__':
    pass
