from flask import Flask
from models.GitLabRepo import list_gitlab_repositories, list_ska_users
import json
from models.User import User
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27018/')
db = client.SKA


@app.route("/gl/project/create", methods=['POST'])
def


@app.route("/db/repos/update", methods=['POST'])
def update_repos():
    repos = list_gitlab_repositories()

    for r in repos:
        try:
            response = db.repositories.update_one({"_id": r.path}, {"$set": r.to_database()}, upsert=True)
        except Exception as e:
            print(e)
            return str(e), 400
    return "Ok"


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
