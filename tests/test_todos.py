import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /todos
# ---------------------------------------------------------------------------

def test_get_todos_happy_path():
    """
    Retrieve all todos and verify a 200 response with an array of todo objects.
    """
    response = requests.get(f"{BASE_URL}/todos")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list), "Response body should be a list"
    assert len(body) > 0, "Todos list should not be empty"
    first_todo = body[0]
    assert "id" in first_todo, "Todo object should contain 'id'"
    assert "title" in first_todo, "Todo object should contain 'title'"
    assert "completed" in first_todo, "Todo object should contain 'completed'"
    assert "userId" in first_todo, "Todo object should contain 'userId'"


# ---------------------------------------------------------------------------
# GET /todos/{id}
# ---------------------------------------------------------------------------

def test_get_todo_happy_path():
    """
    Retrieve a single todo by a valid existing ID (1) and verify a 200 response
    with the correct todo object.
    """
    todo_id = 1
    response = requests.get(f"{BASE_URL}/todos/{todo_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == todo_id, f"Returned todo id should be {todo_id}"
    assert "title" in body, "Todo object should contain 'title'"
    assert "completed" in body, "Todo object should contain 'completed'"
    assert "userId" in body, "Todo object should contain 'userId'"


def test_get_todo_not_found():
    """
    Retrieve a todo by a non-existent ID (99999) and expect a 404 response.
    """
    response = requests.get(f"{BASE_URL}/todos/99999")

    assert response.status_code == 404
    body = response.json()
    # JSONPlaceholder returns an empty object {} for 404s
    assert isinstance(body, dict), "404 response body should be a JSON object"


def test_get_todo_edge_case_boundary_id():
    """
    Retrieve a todo using the boundary ID of 1 (first todo) to verify
    the minimum valid ID works.
    """
    todo_id = 1
    response = requests.get(f"{BASE_URL}/todos/{todo_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == todo_id, "Boundary ID 1 should return the first todo"
    assert "title" in body, "Todo object should contain 'title'"
    assert "completed" in body, "Todo object should contain 'completed'"
