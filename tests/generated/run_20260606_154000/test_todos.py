import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /todos
# ---------------------------------------------------------------------------

def test_get_todos_happy_path():
    """Retrieve all todos and verify a 200 response with a non-empty array
    of todo objects."""
    response = requests.get(f"{BASE_URL}/todos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "id" in first
    assert "title" in first
    assert "completed" in first


# ---------------------------------------------------------------------------
# GET /todos/{id}
# ---------------------------------------------------------------------------

def test_get_todo_happy_path():
    """Retrieve a single todo by valid ID (1) and verify a 200 response
    with the correct todo object."""
    response = requests.get(f"{BASE_URL}/todos/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "title" in data
    assert "completed" in data
    assert "userId" in data


def test_get_todo_not_found():
    """Attempt to retrieve a todo with a non-existent ID (99999) and expect
    a 404 response."""
    response = requests.get(f"{BASE_URL}/todos/99999")
    assert response.status_code == 404
    data = response.json()
    assert data == {} or data is not None


def test_get_todo_edge_case_last_id():
    """Retrieve the todo with the last known valid ID (200) to test the upper
    boundary and verify a 200 response."""
    response = requests.get(f"{BASE_URL}/todos/200")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 200
    assert "title" in data
    assert "completed" in data
