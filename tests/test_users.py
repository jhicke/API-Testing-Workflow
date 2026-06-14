import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------

def test_get_users_happy_path():
    """
    Retrieve all users and verify a 200 response with an array of user objects.
    """
    response = requests.get(f"{BASE_URL}/users")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list), "Response body should be a list"
    assert len(body) > 0, "Users list should not be empty"
    first_user = body[0]
    assert "id" in first_user, "User object should contain 'id'"
    assert "name" in first_user, "User object should contain 'name'"
    assert "email" in first_user, "User object should contain 'email'"
    assert "username" in first_user, "User object should contain 'username'"


# ---------------------------------------------------------------------------
# GET /users/{id}
# ---------------------------------------------------------------------------

def test_get_user_happy_path():
    """
    Retrieve a single user by a valid existing ID (1) and verify a 200 response
    with the correct user object.
    """
    user_id = 1
    response = requests.get(f"{BASE_URL}/users/{user_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user_id, f"Returned user id should be {user_id}"
    assert "name" in body, "User object should contain 'name'"
    assert "email" in body, "User object should contain 'email'"
    assert "username" in body, "User object should contain 'username'"


def test_get_user_not_found():
    """
    Retrieve a user by a non-existent ID (99999) and expect a 404 response.
    """
    response = requests.get(f"{BASE_URL}/users/99999")

    assert response.status_code == 404
    body = response.json()
    # JSONPlaceholder returns an empty object {} for 404s
    assert isinstance(body, dict), "404 response body should be a JSON object"


def test_get_user_edge_case_boundary_id():
    """
    Retrieve a user using the boundary ID of 1 (first user) to verify
    the minimum valid ID works.
    """
    user_id = 1
    response = requests.get(f"{BASE_URL}/users/{user_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user_id, "Boundary ID 1 should return the first user"
    assert "name" in body, "User object should contain 'name'"
    assert "email" in body, "User object should contain 'email'"
