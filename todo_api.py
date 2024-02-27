from flask import Flask, jsonify, request, abort
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

# In-memory database for the purpose of this example
tasks = []


@app.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify({"tasks": tasks})


@app.route("/tasks", methods=["POST"])
def create_task():
    if not request.json or "title" not in request.json:
        abort(400)
    task = {
        "id": len(tasks) + 1,
        "title": request.json["title"],
        "description": request.json.get("description", ""),
        "done": False,
    }
    tasks.append(task)
    return jsonify({"task": task}), 201


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = next((task for task in tasks if task["id"] == task_id), None)
    if task is None:
        abort(404)
    return jsonify({"task": task})


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = next((task for task in tasks if task["id"] == task_id), None)
    if task is None:
        abort(404)
    if not request.json:
        abort(400)
    task["title"] = request.json.get("title", task["title"])
    task["description"] = request.json.get("description", task["description"])
    task["done"] = request.json.get("done", task["done"])
    return jsonify({"task": task})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    global tasks
    tasks = [task for task in tasks if task["id"] != task_id]
    return jsonify({"result": True})


if __name__ == "__main__":
    app.run(debug=True)
