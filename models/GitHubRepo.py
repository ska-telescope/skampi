import subprocess
from github import Github
import gitlab

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

def github_repositories():
    # using username and password
    g = Github("mail", "pass")  # put credentials here

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