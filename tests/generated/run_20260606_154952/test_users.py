import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------

def test_get_users_happy_path():
    """
    Retrieve all users and verify a 200 response with a non-empty array of
    user objects.
    """
    response = requests.get(f"{BASE_URL}/users")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert isinstance(data, list), "Response body should be a list"
    assert len(data) > 0, "Response array should not be empty"
    # Spot-check the first user has expected fields
    first = data[0]
    assert "id" in first, "User object should contain 'id'"
    assert "name" in first, "User object should contain 'name'"


# ---------------------------------------------------------------------------
# GET /users/{id}
# ---------------------------------------------------------------------------

def test_get_user_by_id_happy_path():
    """
    Retrieve a single user by a valid ID and verify a 200 response with the
    correct user object.
    """
    user_id = 1
    response = requests.get(f"{BASE_URL}/users/{user_id}")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert data.get("id") == user_id, (
        f"Returned user id should be {user_id}"
    )
    assert "name" in data, "User object should contain 'name'"


def test_get_user_by_id_not_found():
    """
    Attempt to retrieve a user with a non-existent ID (99999) and expect a
    404 response.
    """
    response = requests.get(f"{BASE_URL}/users/99999")

    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}"
    )
    data = response.json()
    # JSONPlaceholder returns an empty object {} for 404s
    assert isinstance(data, dict), "Response body should be a dict"


def test_get_user_by_id_edge_case_last():
    """
    Retrieve the user with the boundary ID of 10 (last known user) and verify
    a 200 response.
    """
    user_id = 10
    response = requests.get(f"{BASE_URL}/users/{user_id}")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert data.get("id") == user_id, (
        f"Returned user id should be {user_id}"
    )
    assert "name" in data, "User object should contain 'name'"
