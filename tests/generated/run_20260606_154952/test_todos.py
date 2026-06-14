import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /todos
# ---------------------------------------------------------------------------

def test_get_todos_happy_path():
    """
    Retrieve all todos and verify a 200 response with a non-empty array of
    todo objects.
    """
    response = requests.get(f"{BASE_URL}/todos")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert isinstance(data, list), "Response body should be a list"
    assert len(data) > 0, "Response array should not be empty"
    # Spot-check the first todo has expected fields
    first = data[0]
    assert "id" in first, "Todo object should contain 'id'"
    assert "title" in first, "Todo object should contain 'title'"
    assert "completed" in first, "Todo object should contain 'completed'"


# ---------------------------------------------------------------------------
# GET /todos/{id}
# ---------------------------------------------------------------------------

def test_get_todo_by_id_happy_path():
    """
    Retrieve a single todo by a valid ID and verify a 200 response with the
    correct todo object.
    """
    todo_id = 1
    response = requests.get(f"{BASE_URL}/todos/{todo_id}")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert data.get("id") == todo_id, (
        f"Returned todo id should be {todo_id}"
    )
    assert "title" in data, "Todo object should contain 'title'"
    assert "completed" in data, "Todo object should contain 'completed'"


def test_get_todo_by_id_not_found():
    """
    Attempt to retrieve a todo with a non-existent ID (99999) and expect a
    404 response.
    """
    response = requests.get(f"{BASE_URL}/todos/99999")

    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}"
    )
    data = response.json()
    # JSONPlaceholder returns an empty object {} for 404s
    assert isinstance(data, dict), "Response body should be a dict"


def test_get_todo_by_id_edge_case_last():
    """
    Retrieve the todo with the boundary ID of 200 (last known todo) and verify
    a 200 response.
    """
    todo_id = 200
    response = requests.get(f"{BASE_URL}/todos/{todo_id}")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert data.get("id") == todo_id, (
        f"Returned todo id should be {todo_id}"
    )
    assert "title" in data, "Todo object should contain 'title'"
