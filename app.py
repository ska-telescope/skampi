from flask import Flask, request, abort, jsonify, url_for
from models.GitLabRepo import list_gitlab_repositories, list_ska_users, create_gitlab_repo
from models.ReadtheDocsProject import ReadtheDocs, ReadthedocsProject
import json
from models.User import User
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27018/')
db = client.SKA


@app.route("/rtd/project/import", methods=['POST'])
def import_docs():
    test_list = ['name_with_namespace',
                 'repository']
    if not request.json or all(x not in request.json for x in test_list):
        abort(400)
    if 'programming_language' not in request.json:
        prog_lang = "py"
    else:
        prog_lang = request.json['programming_language']
    if 'language' not in request.json:
        lang = "en"
    else:
        lang = request.json['language']

    if 'test' in request.json:
        test_sub = True
    else:
        test_sub = False

    readthedocs_project = ReadthedocsProject(name=request.json['name_with_namespace'],
                                             repo_url=request.json['repository'],
                                             language=lang, programming_language=prog_lang).create_project(test_sub)

    return readthedocs_project


@app.route("/gl/project/create", methods=['POST'])
def create_repo():

    if not request.json or all(x not in request.json for x in ['project_name', 'maintainer_ids']):
        abort(400)
    name = request.json['project_name']
    maintainer_ids = request.json['maintainer_ids']

    if 'template' in request.json:
        template = request.json['template']
    else:
        template = None

    if 'group_id' in request.json:
        result = create_gitlab_repo(name, request.json['group_id'], maintainer_ids)
    else:
        result = create_gitlab_repo(name, maintainer_ids=maintainer_ids, template=template)  # Group ID is ska-telescope - hardcoded

    next_urls = {'import_readthedocs': url_for(import_docs)}
    # next_urls['clone_repo'] = url_for(import_docs)

    result['api_links'] = next_urls

    return jsonify(result)


@app.route("/db/repos/update", methods=['POST'])
def update_repos():
    repos = list_gitlab_repositories()

    for r in repos:
        try:
            response = db.repositories.update_one({"_id": r.path}, {"$set": r.to_database()}, upsert=True)
        except Exception as e:
            print(e)
            return str(e), 400
    return response.status  # let's see if that gives more useful feedback


@app.route("/db/users/update", methods=['POST'])
def update_users():
    users = list_ska_users()

    for u in users:
        user = User(u.id, u.username, u.name, u.avatar_url)
        try:
            response = db.users.update_one({"_id": user.id}, {"$set": user.toDB()}, upsert=True)
        except Exception as e:
            print(e)
            return str(e), 400
    return "Ok"


if __name__ == "__main__":
    app.run(debug=True)
