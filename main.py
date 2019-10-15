
import schedule
import time
import requests
from github import Github
import gitlab
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pprint
        
class Repository:

    def __init__(self,name,github = None,gitlab = None):
        self.name = name
        self.github = github
        self.gitlab = gitlab

    def set_gitlab(self,gitlab):
        self.gitlab = gitlab

    
class GitHubRepo:
    def __init__(self,name):
        self.name = name
        self.mantainers = []
        self.teams = []
    def __str__(self):
        return "Name: " + str(self.name) + " || " + "Mantainers: " + str(self.mantainers)

    def addMantainers(self,mantainers):
        for m in mantainers:
            if not m.login in self.mantainers:   
                self.mantainers.append(m.login)

    def addTeam(self,team):
        self.teams.append(team)

class GitLabRepo:
    def __init__(self,name,mirror,creator):
        self.name = name
        self.mirror = mirror
        self.creator = creator

def GithubRepos():
   # using username and password
    g = Github("dfsn@ua.pt", "Slbbenfica94")   #put credentials here

    teams = g.get_organization("ska-telescope").get_teams()

    repos = {}
    for team in teams:
        for repo in team.get_repos():
            if repos.get(repo.name) == None: 
                repos[repo.name] = GitHubRepo(repo.name)
                repos.get(repo.name).addMantainers(team.get_members("maintainer"))
                repos.get(repo.name).addTeam(team.name)
            else:
                repos.get(repo.name).addMantainers(team.get_members("maintainer"))
                repos.get(repo.name).addTeam(team.name)

    return repos
            

def GitlabRepos():
     # private token or personal token authentication
    gl = gitlab.Gitlab('https://gitlab.com', private_token='MX_2Q5yUqYvHWexVYaxu')   # get your token  here: https://gitlab.com/profile/personal_access_tokens

    group = gl.groups.get(3180705)

    projects = group.projects.list(all=True)

    result = []
    for project in projects:
        creator = gl.users.get(project.creator_id).username
        result.append(GitLabRepo(project.name, project.mirror,creator))

    return result
    


if __name__ == '__main__':

    githubRepos = GithubRepos()
    gitlabRepos = GitlabRepos()

    
    repos = []
    for key in githubRepos.keys():
        hubRepo = githubRepos.get(key)
        
        actualRepo = Repository(hubRepo.name,github= hubRepo)

        for labRepo in gitlabRepos:
            if(labRepo.name == hubRepo.name):
                 actualRepo.set_gitlab(labRepo)
                 gitlabRepos.remove(labRepo)

        repos.append(actualRepo)

    for labRepo in gitlabRepos:
        repos.append(Repository(labRepo.name,gitlab= labRepo))  

    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)         # to get credentials: https://gspread.readthedocs.io/en/latest/oauth2.html
    client = gspread.authorize(creds)
    sheet = client.open_by_key('1avnRJx_HIHoexkPpkYqi8D7n5X0g20aS7WpHPTUMY1Y').sheet1                                       # https://docs.google.com/spreadsheets/d/HERES-THE-ID/edit#gid=0

    index = 2
    for repo in repos:
        # Select a range
        cell_list = sheet.range('A'+str(index)+':F' + str(index))

       
        if(repo.github is not None and repo.gitlab is not None):
            cell_list[0].value = repo.name
            cell_list[1].value = True
            cell_list[2].value = True
            cell_list[3].value = repo.gitlab.mirror
            cell_list[4].value = str(repo.github.mantainers)
            cell_list[5].value = str(repo.github.teams)

            print(str(repo.name) + "\t\t\t\t github: YES \t || gtilab: YES \t || \t admins: " + str(repo.github.mantainers)) 
        elif(repo.github is not None):
            cell_list[0].value = repo.name
            cell_list[1].value = False
            cell_list[2].value = True
            cell_list[3].value = False
            cell_list[4].value = str(repo.github.mantainers)
            cell_list[5].value = str(repo.github.teams)

            print(str(repo.name) + "\t\t\t\t github: YES \t || gtilab: NO \t || \t admins: " + str(repo.github.mantainers)) 
        elif(repo.gitlab is not None):
            cell_list[0].value = repo.name
            cell_list[1].value = True
            cell_list[2].value = False
            cell_list[3].value = repo.gitlab.mirror
            cell_list[4].value = str(repo.gitlab.creator)
            cell_list[5].value = ""

            print(str(repo.name) + "\t\t\t\t github: NO \t || gtilab: YES \t || \t admins: " + str(repo.gitlab.creator)) 


        
        # Update in batch
        sheet.update_cells(cell_list)

        index = index + 1
    
    
    
    
   
