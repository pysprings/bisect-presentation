from hypothesis import settings, strategies as st
from hypothesis import HealthCheck
from hypothesis.strategies import sampled_from
import base64
from hypothesis.stateful import RuleBasedStateMachine, rule, Bundle, initialize
from todo_api import app
...


class TodoAPIStateMachine(RuleBasedStateMachine):
    users = Bundle("users")
    tasks = Bundle("tasks")

    predefined_users = [("john", "hello"), ("susan", "bye")]

    @initialize(target=users, user=sampled_from(predefined_users))
    def add_user(self, user):
        return user

    @rule(target=tasks, user=users)
    def create_task(self, user):
        username, password = user
        with app.test_client() as client:
            response = client.post(
                "/tasks",
                json={"title": "Test Task"},
                headers={
                    "Authorization": "Basic "
                    + base64.b64encode(
                        bytes(username + ":" + password, "ascii")
                    ).decode("ascii")
                },
            )
            assert response.status_code == 201
        assert response.status_code == 201
        return response.json["task"]["id"]

    @rule(task_id=tasks, user=users)
    def delete_task(self, task_id, user):
        username, password = user
        with app.test_client() as client:
            response = client.delete(
                f"/tasks/{task_id}",
                headers={
                    "Authorization": "Basic "
                    + base64.b64encode(
                        bytes(username + ":" + password, "ascii")
                    ).decode("ascii")
                },
            )
            if response.status_code == 404:
                # Task was already deleted, which is fine
                pass
            else:
                assert response.status_code == 200

    @rule(task_id=tasks, user=users)
    def get_task(self, task_id, user):
        username, password = user
        with app.test_client() as client:
            response = client.get(
                f"/tasks/{task_id}",
                headers={
                    "Authorization": "Basic "
                    + base64.b64encode(
                        bytes(username + ":" + password, "ascii")
                    ).decode("ascii")
                },
            )
            if response.status_code == 404:
                # Task does not exist, which is fine
                pass
            else:
                assert response.status_code == 200
                assert "task" in response.json
                assert response.json["task"]["id"] == task_id

    @rule(user=users)
    def get_all_tasks(self, user):
        username, password = user
        with app.test_client() as client:
            response = client.get(
                "/tasks",
                headers={
                    "Authorization": "Basic "
                    + base64.b64encode(
                        bytes(username + ":" + password, "ascii")
                    ).decode("ascii")
                },
            )
            assert response.status_code == 200
            assert "tasks" in response.json
            # Ensure that all tasks in the response belong to the user
            for task in response.json["tasks"]:
                assert task["created_by"] == username

    @rule(task_id=tasks, user=users)
    def toggle_task_done(self, task_id, user):
        username, password = user
        with app.test_client() as client:
            # First, get the current status of the task
            get_response = client.get(
                f"/tasks/{task_id}",
                headers={
                    "Authorization": "Basic "
                    + base64.b64encode(
                        bytes(username + ":" + password, "ascii")
                    ).decode("ascii")
                },
            )
            if get_response.status_code == 404:
                # Task does not exist, which is fine
                pass
            else:
                current_done_status = get_response.json["task"]["done"]
                # Now, toggle the done status of the task
                update_response = client.put(
                    f"/tasks/{task_id}",
                    json={
                        "done": not current_done_status,
                    },
                    headers={
                        "Authorization": "Basic "
                        + base64.b64encode(
                            bytes(username + ":" + password, "ascii")
                        ).decode("ascii")
                    },
                )
                assert update_response.status_code == 200
                assert "task" in update_response.json
                assert update_response.json["task"]["done"] != current_done_status

    @rule(task_id=tasks, user=users, title=st.text(), description=st.text(), done=st.booleans())
    def update_task(self, task_id, user, title, description, done):
        username, password = user
        with app.test_client() as client:
            response = client.put(
                f"/tasks/{task_id}",
                json={
                    "title": title,
                    "description": description,
                    "done": done,
                },
                headers={
                    "Authorization": "Basic "
                    + base64.b64encode(
                        bytes(username + ":" + password, "ascii")
                    ).decode("ascii")
                },
            )
            if response.status_code == 404:
                # Task does not exist, which is fine
                pass
            else:
                assert response.status_code == 200
                assert "task" in response.json
                updated_task = response.json["task"]
                assert updated_task["id"] == task_id
                assert updated_task["title"] == title
                assert updated_task["description"] == description
                assert updated_task["done"] == done

    # Additional rules for updating and fetching tasks can be added here


    # Additional rules for stateful testing
    @rule(user=users)
    def check_user_exists(self, user):
        username, password = user
        with app.test_client() as client:
            response = client.get(
                "/users",
                headers={
                    "Authorization": "Basic "
                    + base64.b64encode(
                        bytes(username + ":" + password, "ascii")
                    ).decode("ascii")
                },
            )
            assert response.status_code == 200
            assert any(u["username"] == username for u in response.json["users"])

    @rule(user=users, title=st.text(), description=st.text())
    def create_and_get_task(self, user, title, description):
        username, password = user
        with app.test_client() as client:
            # Create a new task
            create_response = client.post(
                "/tasks",
                json={"title": title, "description": description},
                headers={
                    "Authorization": "Basic "
                    + base64.b64encode(
                        bytes(username + ":" + password, "ascii")
                    ).decode("ascii")
                },
            )
            assert create_response.status_code == 201
            task_id = create_response.json["task"]["id"]
            # Fetch the newly created task
            get_response = client.get(
                f"/tasks/{task_id}",
                headers={
                    "Authorization": "Basic "
                    + base64.b64encode(
                        bytes(username + ":" + password, "ascii")
                    ).decode("ascii")
                },
            )
            assert get_response.status_code == 200
            assert get_response.json["task"]["title"] == title
            assert get_response.json["task"]["description"] == description

TestTodoAPI = TodoAPIStateMachine.TestCase
TestTodoAPI.settings = settings(max_examples=50, stateful_step_count=10, suppress_health_check=[HealthCheck.too_slow])

if __name__ == "__main__":
    TestTodoAPI().runTest()
