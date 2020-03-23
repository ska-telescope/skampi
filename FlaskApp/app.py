from flask import Flask, request, abort, jsonify, url_for
from models.GitLabRepo import list_gitlab_repositories, list_ska_users, create_gitlab_repo
from models.ReadtheDocsProject import create_readthedocs_project
from models.User import User
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27018/')
db = client.SKA


@app.route("/rtd/project/import", methods=['POST'])
def import_docs():
    test_list = ['name_with_namespace', 'repository']

    if not request.json or all(x not in request.json for x in test_list):
        abort(400)

    return create_readthedocs_project(request.json)


@app.route("/gl/project/create", methods=['POST'])
def create_repo():

    if not request.json or all(x not in request.json for x in ['project_name', 'maintainer_ids']):
        abort(400)

    result = create_gitlab_repo(request.json)

    next_urls = {'import_readthedocs': url_for('import_docs', _external=True)}
    # next_urls['clone_repo'] = url_for(import_docs)

    result['_api_links'] = next_urls

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
    return response.status  #TODO: Only last reponse to be returned - probably OK but let's discuss later


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
