"""
Unit tests for TaskFlow API

Run with: pytest tests/ -v
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, Task


@pytest.fixture
def client():
    """Create a test client with a fresh database."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()

        with app.test_client() as client:
            yield client

        db.drop_all()


@pytest.fixture
def auth_token(client):
    """Create a user and return their auth token."""
    # Register user
    reg_response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })

    # Login and get token
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })

    data = response.get_json()
    return data["token"]


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """GET / should return healthy status."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.get_json()["status"] == "healthy"


class TestAuth:
    """Tests for authentication endpoints."""

    def test_register_success(self, client):
        """POST /auth/register should create a new user."""
        response = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "secret123"
        })
        assert response.status_code == 201
        assert "user" in response.get_json()

    def test_register_missing_email(self, client):
        """POST /auth/register without email should return 400."""
        response = client.post("/auth/register", json={
            "password": "secret123"
        })
        assert response.status_code == 400

    def test_register_short_password(self, client):
        """POST /auth/register with short password should return 400."""
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "short"
        })
        assert response.status_code == 400

    def test_register_duplicate_email(self, client):
        """POST /auth/register with existing email should return 400."""
        client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 400

    def test_login_success(self, client):
        """POST /auth/login with valid credentials should return token."""
        # Register first
        client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })

        # Then login
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "token" in response.get_json()

    def test_login_wrong_password(self, client):
        """POST /auth/login with wrong password should return 401."""
        client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """POST /auth/login for non-existent user should return 401."""
        response = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "password123"
        })
        assert response.status_code == 401


class TestTasks:
    """Tests for task endpoints."""

    def test_get_tasks_unauthorized(self, client):
        """GET /tasks without token should return 401."""
        response = client.get("/tasks")
        assert response.status_code == 401

    def test_get_tasks_empty(self, client, auth_token):
        """GET /tasks should return empty list for new user."""
        response = client.get("/tasks", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        assert response.get_json()["data"] == []

    def test_create_task(self, client, auth_token):
        """POST /tasks should create a new task."""
        response = client.post("/tasks",
            json={"title": "Test Task"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        assert response.get_json()["title"] == "Test Task"

    def test_create_task_missing_title(self, client, auth_token):
        """POST /tasks without title should return 400."""
        response = client.post("/tasks",
            json={"description": "No title here"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400

    def test_get_single_task(self, client, auth_token):
        """GET /tasks/:id should return the task."""
        # Create a task first
        create_response = client.post("/tasks",
            json={"title": "Test Task"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        task_id = create_response.get_json()["id"]

        # Get the task
        response = client.get(f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.get_json()["title"] == "Test Task"

    def test_get_nonexistent_task(self, client, auth_token):
        """GET /tasks/:id for non-existent task should return 404."""
        response = client.get("/tasks/9999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_update_task(self, client, auth_token):
        """PUT /tasks/:id should update the task."""
        # Create a task
        create_response = client.post("/tasks",
            json={"title": "Original Title"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        task_id = create_response.get_json()["id"]

        # Update the task
        response = client.put(f"/tasks/{task_id}",
            json={"title": "Updated Title", "completed": True},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.get_json()["title"] == "Updated Title"
        assert response.get_json()["completed"] is True

    def test_delete_task(self, client, auth_token):
        """DELETE /tasks/:id should delete the task."""
        # Create a task
        create_response = client.post("/tasks",
            json={"title": "To Delete"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        task_id = create_response.get_json()["id"]

        # Delete the task
        response = client.delete(f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 404


class TestTaskFiltering:
    """Tests for task filtering and pagination."""

    def test_filter_by_completed(self, client, auth_token):
        """GET /tasks?completed=true should filter tasks."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create tasks
        client.post("/tasks", json={"title": "Incomplete"}, headers=headers)
        create_response = client.post("/tasks", json={"title": "Complete"}, headers=headers)

        # Mark one as complete
        task_id = create_response.get_json()["id"]
        client.put(f"/tasks/{task_id}", json={"completed": True}, headers=headers)

        # Filter by completed
        response = client.get("/tasks?completed=true", headers=headers)
        tasks = response.get_json()["data"]
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Complete"

    def test_pagination(self, client, auth_token):
        """GET /tasks with pagination should limit results."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create 5 tasks
        for i in range(5):
            client.post("/tasks", json={"title": f"Task {i}"}, headers=headers)

        # Get first page with limit 2
        response = client.get("/tasks?page=1&limit=2", headers=headers)
        data = response.get_json()
        assert len(data["data"]) == 2
        assert data["pagination"]["total_items"] == 5
        assert data["pagination"]["has_next"] is True


class TestUserIsolation:
    """Tests for user data isolation."""

    def test_user_cannot_see_other_tasks(self, client):
        """Users should only see their own tasks."""
        # Create first user and task
        client.post("/auth/register", json={
            "email": "user1@example.com",
            "password": "password123"
        })
        login1 = client.post("/auth/login", json={
            "email": "user1@example.com",
            "password": "password123"
        })
        token1 = login1.get_json()["token"]

        client.post("/tasks",
            json={"title": "User 1 Task"},
            headers={"Authorization": f"Bearer {token1}"}
        )

        # Create second user
        client.post("/auth/register", json={
            "email": "user2@example.com",
            "password": "password123"
        })
        login2 = client.post("/auth/login", json={
            "email": "user2@example.com",
            "password": "password123"
        })
        token2 = login2.get_json()["token"]

        # User 2 should see empty task list
        response = client.get("/tasks",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.get_json()["data"] == []

    def test_user_cannot_access_other_task(self, client):
        """User should get 403 when accessing another user's task."""
        # Create first user and task
        client.post("/auth/register", json={
            "email": "user1@example.com",
            "password": "password123"
        })
        login1 = client.post("/auth/login", json={
            "email": "user1@example.com",
            "password": "password123"
        })
        token1 = login1.get_json()["token"]

        create_response = client.post("/tasks",
            json={"title": "User 1 Task"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        task_id = create_response.get_json()["id"]

        # Create second user
        client.post("/auth/register", json={
            "email": "user2@example.com",
            "password": "password123"
        })
        login2 = client.post("/auth/login", json={
            "email": "user2@example.com",
            "password": "password123"
        })
        token2 = login2.get_json()["token"]

        # User 2 tries to access User 1's task
        response = client.get(f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 403
