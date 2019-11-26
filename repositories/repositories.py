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
    def __init__(self, name, path, creator=None, mirror=None):
        self.name = name
        self.mirror = mirror
        self.creator = creator
        self.path = path


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

    group = gl.groups.get(3180705) #Group ID of ska-telescope

    projects = group.projects.list(all=True, order_by="name", sort="asc")

    result = []
    for project in projects:
        creator = gl.users.get(project.creator_id).username
        result.append(GitLabRepo(name=project.name, path=project.path))

    return result

def list_ska_users():
    # private token or personal token authentication
    gl = gitlab.Gitlab('https://gitlab.com',
                       private_token='MX_2Q5yUqYvHWexVYaxu')  # get your token  here: https://gitlab.com/profile/personal_access_tokens

    # developer.skatelescope.org project ID
    return gl.projects.get(9070656).members.all(all=True)


def create_gitlab_repo(name, group_id=3180705, maintainer_ids=[None]):
    # private token or personal token authentication
    gl = gitlab.Gitlab('https://gitlab.com',
                       private_token='MX_2Q5yUqYvHWexVYaxu')  # get your token  here: https://gitlab.com/profile/personal_access_tokens

    project = gl.projects.create({'name': name, 'namespace_id': group_id})

    # Share project with SKA Reporters group:
    project.share(6051772, gitlab.REPORTER_ACCESS)

    # Share project with SKA Developers group:
    project.share(6051706, gitlab.DEVELOPER_ACCESS)

    # Add maintainer users
    if maintainer_ids[0] is not None:
        for user_id in maintainer_ids:
            member = project.members.get(user_id)
            member.access_level = gitlab.MAINTAINER_ACCESS
            member.save()

    return project


if __name__ == '__main__':
    # print(name for name in list_gitlab_repositories())

    project = create_gitlab_repo("Test AutoRepo")

    print(project)
