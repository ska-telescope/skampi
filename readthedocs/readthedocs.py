import json

from readthedocs import conf
import requests


class ReadtheDocs():
    def __init__(self, token=conf.readthedocs_token):
        self.headers = {"Authorization": "Token " + token}
        self.base_url = "https://readthedocs.org/api/v3/"

    def base(self):
        """Simple query just to check connection"""
        return requests.get(self.base_url)

    def extend_headers(self, ):
        self.headers['Content-Type'] = "application/json"

    def get_projects_for_user(self):
        url = self.base_url + 'projects'
        # TODO: pagination?
        response = requests.get(url, headers=self.headers)
        result = response.json()

        all_projects = result['results']

        return all_projects

    def make_subproject(self, parent, child):
        url = self.base_url + 'projects/' + parent + '/subprojects/'
        self.extend_headers()
        body = {
            "child": child,
            "alias": child
        }
        payload = json.dumps(body)
        response = requests.post(url, data=payload, headers=self.headers)
        return response


class ReadthedocsProject():
    def __init__(self, name, repo_url, slug="", url="", language="en", programming_language="words"):
        self.slug = slug
        self.name = name
        self.url = url
        self.repo_url = repo_url
        self.is_subproject = False
        self.language = language
        self.programming_language = programming_language

    def get_subproject(self, subproject_of):
        if subproject_of is None:
            self.is_subproject = False
        else:
            if subproject_of['id'] == 216769:  # developer portal
                self.is_subproject = True

    def create_project(self):
        """
        Create a Project on ReadtheDocs. Minimal list of fields to be included:
        {
        "name": "Test Project",
        "repository": {
            "url": "https://github.com/readthedocs/template",
            "type": "git"
        },
        "homepage": "http://template.readthedocs.io/",
        "programming_language": "py",
        "language": "es"
    }
        :return: Response Text
        """

        rtd = ReadtheDocs()

        body = {"name": self.name}

        repodetails = {"url": self.repo_url, "type": "git"}
        body["repository"] = repodetails

        body["programming_language"] = self.programming_language
        body["language"] = self.language

        payload = json.dumps(body)

        url = rtd.base_url + 'projects/'

        # specify JSON app type
        rtd.extend_headers()
        response = requests.request("POST", url, data=payload, headers=rtd.headers)

        if response.status_code == 201:
            result = response.text
        else:
            result = response.reason
        return result


def list_of_projects(non_sub_only=False):
    readthedocs = ReadtheDocs()

    projects = []

    results = readthedocs.get_projects_for_user

    for res in results:
        rtd_project = ReadthedocsProject(res['name'], res['slug'], res['urls']['documentation'],
                                         res['repository']['url'])
        rtd_project.get_subproject(res['subproject_of'])

        if non_sub_only:
            if not rtd_project.is_subproject:
                projects.append(rtd_project)
        else:
            projects.append(rtd_project)

    return projects


def make_subprojects(parent="developerskatelescopeorg", project_slugs=['my-mac']):
    """ Make subprojects of each of the ReadtheDocs projects in the list projects

    @:param: projects: list of slugs of projects to be made subprojects
    @:param: parent: parent project
    """

    if project_slugs is None:
        project_slugs = []

    readthedocs = ReadtheDocs()
    for slug in project_slugs:
        print(readthedocs.make_subproject(parent, slug).status_code)


if __name__ == '__main__':
    # pp.pprint([proj.name for proj in list_of_projects(True)])
    # pp.pprint(readthedocs.get_projects_for_user)

    # make_subproject()
    rtdp = ReadthedocsProject("My Mac", programming_language="py",
                              repo_url="https://github.com/thermostatix/mymac/tree/master")
    print(rtdp.create_project())
    make_subprojects()

    # var = rtdp.explanation()
    # print(json.dumps(var))
