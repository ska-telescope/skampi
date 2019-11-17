import json

import conf
import requests
import pprint as pp


class ReadtheDocs():
    def __init__(self, token=conf.readthedocs_token):
        self.header = {"Authorization": "Token " + token}
        self.base_url = "https://readthedocs.org/api/v3/"

    def base(self):
        return requests.get(self.base_url)

    @property
    def get_projects_for_user(self):
        url = self.base_url + 'projects'
        # TODO: pagination?
        response = requests.get(url, headers=self.header)
        result = response.json()

        all_projects = result['results']

        return all_projects

    @property
    def users(self):
        users = {"users": [
            {
                "username": "flyingfrog"
            },
            {
                "username": "matteo1981"
            },
            {
                "username": "jbmorgado"
            },
            {
                "username": "bartashevich"
            },
            {
                "username": "adriaan-sac"
            },
            {
                "username": "domingosnunes"
            }
        ]}
        return json.dumps(users)


class ReadthedocsProject():
    def __init__(self, name, slug, url, repo_url):
        self.slug = slug
        self.name = name
        self.url = url
        self.repository_url = repo_url
        self.is_subproject = False

    def get_subproject(self, subproject_of):
        if subproject_of is None:
            self.is_subproject = False
        else:
            if subproject_of['id'] == 216769:  # developer portal
                self.is_subproject = True


def list_of_projects():
    readthedocs = ReadtheDocs()

    projects = []

    results = readthedocs.get_projects_for_user

    for res in results:
        rtd_project = ReadthedocsProject(res['name'], res['slug'], res['urls']['documentation'],
                                         res['repository']['url'])
        rtd_project.get_subproject(res['subproject_of'])

        projects.append(rtd_project)

    return projects


if __name__ == '__main__':
    pass
    pp.pprint([proj.name for proj in list_of_projects()])
    # pp.pprint(readthedocs.get_projects_for_user)
