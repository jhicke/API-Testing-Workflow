import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------

def test_get_users_happy_path():
    """Retrieve all users and verify a 200 response with a non-empty array
    of user objects."""
    response = requests.get(f"{BASE_URL}/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "id" in first
    assert "name" in first


# ---------------------------------------------------------------------------
# GET /users/{id}
# ---------------------------------------------------------------------------

def test_get_user_happy_path():
    """Retrieve a single user by valid ID (1) and verify a 200 response
    with the correct user object."""
    response = requests.get(f"{BASE_URL}/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "name" in data
    assert "email" in data


def test_get_user_not_found():
    """Attempt to retrieve a user with a non-existent ID (99999) and expect
    a 404 response."""
    response = requests.get(f"{BASE_URL}/users/99999")
    assert response.status_code == 404
    data = response.json()
    assert data == {} or data is not None


def test_get_user_edge_case_boundary_zero():
    """Retrieve the user with the boundary ID of 0 (below minimum valid range)
    and expect a 404 response."""
    response = requests.get(f"{BASE_URL}/users/0")
    assert response.status_code == 404
    data = response.json()
    assert data == {} or data is not None
