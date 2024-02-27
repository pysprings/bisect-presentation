from flask import Flask, jsonify, request, abort
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {"john": "hello", "susan": "bye"}


@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username


# In-memory database for the purpose of this example
tasks = []


@app.route("/tasks", methods=["GET"])
@auth.login_required
def get_tasks():
    user = auth.current_user()
    user_tasks = [task for task in tasks if task["created_by"] == user]
    return jsonify({"tasks": user_tasks})


@app.route("/tasks", methods=["POST"])
@auth.login_required
def create_task():
    if not request.json or "title" not in request.json:
        abort(400)
    user = auth.current_user()
    task = {
        "id": len(tasks) + 1,
        "title": request.json["title"],
        "description": request.json.get("description", ""),
        "done": False,
        "created_by": user,
    }
    tasks.append(task)
    return jsonify({"task": task}), 201


@app.route("/tasks/<int:task_id>", methods=["GET"])
@auth.login_required
def get_task(task_id):
    task = next((task for task in tasks if task["id"] == task_id), None)
    user = auth.current_user()
    if task is None:
        abort(404)
    return jsonify({"task": task})


@app.route("/tasks/<int:task_id>", methods=["PUT"])
@auth.login_required
def update_task(task_id):
    task = next((task for task in tasks if task["id"] == task_id), None)
    user = auth.current_user()
    if task is None:
        abort(404)
    if not request.json:
        abort(400)
    task["title"] = request.json.get("title", task["title"])
    task["description"] = request.json.get("description", task["description"])
    task["done"] = request.json.get("done", task["done"])
    return jsonify({"task": task})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@auth.login_required
def delete_task(task_id):
    global tasks
    user = auth.current_user()
    task = next((task for task in tasks if task["id"] == task_id and task["created_by"] == user), None)
    if task:
        tasks.remove(task)
    else:
        abort(404)
    return jsonify({"result": True})


if __name__ == "__main__":
    app.run(debug=True)
