import json

import conf
import requests


class ReadtheDocs:
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

    def make_subproject(self, parent, child, alias):
        url = self.base_url + 'projects/' + parent + '/subprojects/'
        self.extend_headers()
        body = {
            "child": child,
            "alias": alias
        }
        payload = json.dumps(body)
        response = requests.post(url, data=payload, headers=self.headers)
        return response


