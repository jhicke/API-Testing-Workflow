import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /posts
# ---------------------------------------------------------------------------

def test_get_posts_happy_path():
    """Retrieve all posts and verify a 200 response with an array of post objects."""
    response = requests.get(f"{BASE_URL}/posts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_posts_edge_case():
    """Retrieve all posts and verify the response is a non-empty array containing
    objects with id, userId, title, and body fields."""
    response = requests.get(f"{BASE_URL}/posts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "id" in first
    assert "userId" in first
    assert "title" in first
    assert "body" in first


# ---------------------------------------------------------------------------
# POST /posts
# ---------------------------------------------------------------------------

def test_post_posts_happy_path():
    """Create a new post with all required fields and verify a 201 response
    with the created post including an assigned id."""
    payload = {
        "title": "Test Post Title",
        "body": "This is the body of the test post.",
        "userId": 1,
    }
    response = requests.post(f"{BASE_URL}/posts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["body"] == payload["body"]
    assert data["userId"] == payload["userId"]


def test_post_posts_invalid_input_missing_fields():
    """Attempt to create a post with missing required fields and expect a 4xx error.

    NOTE: JSONPlaceholder is a mock API that accepts any payload and returns 201.
    This test documents the expected strict-API behaviour (400) but marks itself
    as xfail because the live server does not enforce field validation.
    """
    pytest.xfail(
        "JSONPlaceholder does not validate missing fields; "
        "returns 201 instead of 400."
    )
    payload = {}
    response = requests.post(f"{BASE_URL}/posts", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data is not None


def test_post_posts_invalid_input_wrong_types():
    """Attempt to create a post with wrong types (userId as a string) and expect
    a 4xx error.

    NOTE: JSONPlaceholder is a mock API that accepts any payload and returns 201.
    This test documents the expected strict-API behaviour (400) but marks itself
    as xfail because the live server does not enforce type validation.
    """
    pytest.xfail(
        "JSONPlaceholder does not validate field types; "
        "returns 201 instead of 400."
    )
    payload = {
        "title": 12345,
        "body": "Valid body text",
        "userId": "not-an-integer",
    }
    response = requests.post(f"{BASE_URL}/posts", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data is not None


def test_post_posts_edge_case_long_body():
    """Create a post with an extremely long title and body to test boundary
    handling on string fields."""
    long_body = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
        "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
        "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum."
    )
    payload = {
        "title": "A",
        "body": long_body,
        "userId": 1,
    }
    response = requests.post(f"{BASE_URL}/posts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["body"] == payload["body"]


# ---------------------------------------------------------------------------
# GET /posts/{id}
# ---------------------------------------------------------------------------

def test_get_post_happy_path():
    """Retrieve a single post by a valid ID (1) and verify a 200 response
    with the correct post object."""
    response = requests.get(f"{BASE_URL}/posts/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "title" in data
    assert "body" in data
    assert "userId" in data


def test_get_post_not_found():
    """Attempt to retrieve a post with a non-existent ID (99999) and expect
    a 404 response."""
    response = requests.get(f"{BASE_URL}/posts/99999")
    assert response.status_code == 404
    data = response.json()
    assert data == {} or data is not None


def test_get_post_invalid_input_string_id():
    """Attempt to retrieve a post using a non-integer ID (a string) and expect
    a 4xx error."""
    response = requests.get(f"{BASE_URL}/posts/abc")
    assert response.status_code == 404
    data = response.json()
    assert data is not None


def test_get_post_edge_case_first_id():
    """Retrieve the post with the boundary ID of 1 (first post) and verify
    a 200 response."""
    response = requests.get(f"{BASE_URL}/posts/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "title" in data


def test_get_post_edge_case_last_id():
    """Retrieve the post with the last known valid ID (100) to test upper
    boundary and verify a 200 response."""
    response = requests.get(f"{BASE_URL}/posts/100")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 100
    assert "title" in data


# ---------------------------------------------------------------------------
# PUT /posts/{id}
# ---------------------------------------------------------------------------

def test_put_post_happy_path():
    """Fully replace an existing post (ID 1) with all required fields and
    verify a 200 response with the updated post."""
    payload = {
        "id": 1,
        "title": "Updated Post Title",
        "body": "This is the fully updated body of the post.",
        "userId": 1,
    }
    response = requests.put(f"{BASE_URL}/posts/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == payload["title"]
    assert data["body"] == payload["body"]
    assert data["userId"] == payload["userId"]


def test_put_post_invalid_input_missing_fields():
    """Attempt to replace a post (ID 1) while omitting all required fields
    and expect a 4xx error.

    NOTE: JSONPlaceholder is a mock API that accepts any payload and returns 200.
    This test documents the expected strict-API behaviour (400) but marks itself
    as xfail because the live server does not enforce field validation.
    """
    pytest.xfail(
        "JSONPlaceholder does not validate missing fields on PUT; "
        "returns 200 instead of 400."
    )
    payload = {"id": 1}
    response = requests.put(f"{BASE_URL}/posts/1", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data is not None


def test_put_post_edge_case_minimal_data():
    """Replace a post (ID 1) with minimal valid data — single-character title
    and body — to test boundary string values."""
    payload = {
        "id": 1,
        "title": "X",
        "body": "Y",
        "userId": 1,
    }
    response = requests.put(f"{BASE_URL}/posts/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "X"
    assert data["body"] == "Y"


# ---------------------------------------------------------------------------
# PATCH /posts/{id}
# ---------------------------------------------------------------------------

def test_patch_post_happy_path_title():
    """Partially update an existing post (ID 1) by changing only the title
    and verify a 200 response."""
    payload = {"title": "Partially Updated Title"}
    response = requests.patch(f"{BASE_URL}/posts/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == payload["title"]


def test_patch_post_happy_path_body():
    """Partially update an existing post (ID 1) by changing only the body
    and verify a 200 response."""
    payload = {"body": "Only the body has been updated in this patch request."}
    response = requests.patch(f"{BASE_URL}/posts/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["body"] == payload["body"]


def test_patch_post_edge_case_empty_payload():
    """Send a PATCH request to an existing post (ID 1) with an empty body
    payload and verify the API handles it gracefully with a 200."""
    payload = {}
    response = requests.patch(f"{BASE_URL}/posts/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


# ---------------------------------------------------------------------------
# DELETE /posts/{id}
# ---------------------------------------------------------------------------

def test_delete_post_happy_path():
    """Delete an existing post by valid ID (1) and verify a 200 response
    with an empty object."""
    response = requests.delete(f"{BASE_URL}/posts/1")
    assert response.status_code == 200
    data = response.json()
    assert data == {}


def test_delete_post_not_found():
    """Attempt to delete a post with a non-existent ID (99999) and expect
    a 404 response.

    NOTE: JSONPlaceholder returns 200 for all DELETE requests regardless of
    whether the resource exists.  This test documents the expected strict-API
    behaviour (404) but marks itself as xfail because the live server does not
    enforce existence checks on DELETE.
    """
    pytest.xfail(
        "JSONPlaceholder returns 200 for DELETE on non-existent IDs "
        "instead of 404."
    )
    response = requests.delete(f"{BASE_URL}/posts/99999")
    assert response.status_code == 404
    data = response.json()
    assert data is not None
