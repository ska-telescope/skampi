import subprocess
from github import Github
import gitlab

class GitLabRepo:
    def __init__(self, name=None, path=None, creator=None, mirror=None):
        self.name = name
        self.mirror = mirror
        self.creator = creator
        self.path = path

    def toDB(self):
        return {
            "_id": self.path,
            "name": self.name,
            "creator": self.creator,
            "mirror": self.mirror
        }


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