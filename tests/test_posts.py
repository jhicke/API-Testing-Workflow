import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /posts
# ---------------------------------------------------------------------------

def test_get_posts_happy_path():
    """
    Retrieve all posts and verify a 200 response with an array of post objects.
    """
    response = requests.get(f"{BASE_URL}/posts")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list), "Response body should be a list"
    assert len(body) > 0, "Posts list should not be empty"
    first_post = body[0]
    assert "id" in first_post, "Post object should contain 'id'"
    assert "title" in first_post, "Post object should contain 'title'"
    assert "body" in first_post, "Post object should contain 'body'"
    assert "userId" in first_post, "Post object should contain 'userId'"


def test_get_posts_edge_case_unknown_param():
    """
    Retrieve all posts with an unexpected query parameter;
    API should ignore it and still return 200.
    """
    response = requests.get(f"{BASE_URL}/posts", params={"unknownParam": "test"})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list), "Response body should be a list even with unknown param"
    assert len(body) > 0, "Posts list should not be empty"
    assert "id" in body[0], "Post object should contain 'id'"


# ---------------------------------------------------------------------------
# POST /posts
# ---------------------------------------------------------------------------

def test_post_posts_happy_path():
    """
    Create a new post with all required fields and verify a 201 response
    with the created resource including an assigned id.
    """
    payload = {
        "title": "My New Post",
        "body": "This is the body of my new post.",
        "userId": 1,
    }
    response = requests.post(f"{BASE_URL}/posts", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert "id" in body, "Created post should have an 'id' field"
    assert body["title"] == payload["title"], "Returned title should match sent title"
    assert body["body"] == payload["body"], "Returned body should match sent body"
    assert body["userId"] == payload["userId"], "Returned userId should match sent userId"


def test_post_posts_invalid_input_missing_fields():
    """
    Attempt to create a post with missing required fields (title and body omitted);
    JSONPlaceholder is a mock API that does not enforce validation and will
    return 201 for any POST payload.
    """
    payload = {"userId": 1}
    response = requests.post(f"{BASE_URL}/posts", json=payload)

    assert response.status_code == 201, (
        f"Expected 201 from JSONPlaceholder mock, got {response.status_code}. "
        "JSONPlaceholder does not enforce validation."
    )
    body = response.json()
    assert body is not None, "Response body should not be None"


def test_post_posts_invalid_input_wrong_type_userid():
    """
    Attempt to create a post with wrong type for userId (string instead of integer);
    JSONPlaceholder is a mock API that does not enforce type validation and
    will return 201.
    """
    payload = {
        "title": "Bad Type Post",
        "body": "Some body text.",
        "userId": "not-an-integer",
    }
    response = requests.post(f"{BASE_URL}/posts", json=payload)

    assert response.status_code == 201, (
        f"Expected 201 from JSONPlaceholder mock, got {response.status_code}. "
        "JSONPlaceholder does not enforce type validation."
    )
    body = response.json()
    assert body is not None, "Response body should not be None"


def test_post_posts_edge_case_empty_strings():
    """
    Create a post with an empty string for title and body to test boundary
    string values; expect 201.
    """
    payload = {"title": "", "body": "", "userId": 1}
    response = requests.post(f"{BASE_URL}/posts", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert "id" in body, "Created post should have an 'id' field"
    assert body["title"] == "", "Returned title should be an empty string"
    assert body["body"] == "", "Returned body should be an empty string"


# ---------------------------------------------------------------------------
# GET /posts/{id}
# ---------------------------------------------------------------------------

def test_get_post_happy_path():
    """
    Retrieve a single post by a valid existing ID (1) and verify a 200 response
    with the correct post object.
    """
    post_id = 1
    response = requests.get(f"{BASE_URL}/posts/{post_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == post_id, f"Returned post id should be {post_id}"
    assert "title" in body, "Post object should contain 'title'"
    assert "body" in body, "Post object should contain 'body'"
    assert "userId" in body, "Post object should contain 'userId'"


def test_get_post_not_found():
    """
    Retrieve a post by a non-existent ID (99999) and expect a 404 response.
    """
    response = requests.get(f"{BASE_URL}/posts/99999")

    assert response.status_code == 404
    body = response.json()
    # JSONPlaceholder returns an empty object {} for 404s
    assert isinstance(body, dict), "404 response body should be a JSON object"


def test_get_post_invalid_input_non_numeric_id():
    """
    Retrieve a post using a non-numeric ID (string) in the path;
    expect a 4xx error (404 from JSONPlaceholder).
    """
    response = requests.get(f"{BASE_URL}/posts/abc")

    assert response.status_code == 404
    body = response.json()
    assert isinstance(body, dict), "Response body should be a JSON object"


def test_get_post_edge_case_boundary_id():
    """
    Retrieve a post using the boundary ID of 1 (first post) to verify
    the minimum valid ID works.
    """
    post_id = 1
    response = requests.get(f"{BASE_URL}/posts/{post_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == post_id, "Boundary ID 1 should return the first post"
    assert "title" in body, "Post object should contain 'title'"


# ---------------------------------------------------------------------------
# PUT /posts/{id}
# ---------------------------------------------------------------------------

def test_put_post_happy_path():
    """
    Fully replace an existing post (ID 1) with all required fields and verify
    a 200 response with the updated resource.
    """
    post_id = 1
    payload = {
        "id": post_id,
        "title": "Updated Post Title",
        "body": "This is the fully updated body content.",
        "userId": 1,
    }
    response = requests.put(f"{BASE_URL}/posts/{post_id}", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == post_id, f"Returned post id should be {post_id}"
    assert body["title"] == payload["title"], "Returned title should match updated title"
    assert body["body"] == payload["body"], "Returned body should match updated body"
    assert body["userId"] == payload["userId"], "Returned userId should match"


def test_put_post_not_found():
    """
    Attempt to fully replace a post with a non-existent ID (99999);
    JSONPlaceholder returns 200 for PUT on non-existent IDs.
    """
    payload = {
        "id": 99999,
        "title": "Ghost Post",
        "body": "This post does not exist.",
        "userId": 1,
    }
    response = requests.put(f"{BASE_URL}/posts/99999", json=payload)

    assert response.status_code == 200, (
        f"Expected 200 from JSONPlaceholder mock, got {response.status_code}. "
        "JSONPlaceholder does not enforce existence checks."
    )
    body = response.json()
    assert isinstance(body, dict), "Response body should be a JSON object"


def test_put_post_invalid_input_missing_body_field():
    """
    Attempt to fully replace a post (ID 1) with missing required fields
    (body omitted); JSONPlaceholder does not enforce validation and will return 200.
    """
    payload = {"id": 1, "title": "Incomplete Update", "userId": 1}
    response = requests.put(f"{BASE_URL}/posts/1", json=payload)

    assert response.status_code == 200, (
        f"Expected 200 from JSONPlaceholder mock, got {response.status_code}. "
        "JSONPlaceholder does not enforce validation."
    )
    body = response.json()
    assert body is not None, "Response body should not be None"


# ---------------------------------------------------------------------------
# PATCH /posts/{id}
# ---------------------------------------------------------------------------

def test_patch_post_happy_path():
    """
    Partially update an existing post (ID 1) by changing only the title
    and verify a 200 response.
    """
    post_id = 1
    payload = {"title": "Partially Updated Title"}
    response = requests.patch(f"{BASE_URL}/posts/{post_id}", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == post_id, f"Returned post id should be {post_id}"
    assert body["title"] == payload["title"], "Returned title should match patched title"


def test_patch_post_not_found():
    """
    Attempt to partially update a post with a non-existent ID (99999);
    JSONPlaceholder returns 200 for PATCH on non-existent IDs.
    """
    payload = {"title": "Patch on Ghost"}
    response = requests.patch(f"{BASE_URL}/posts/99999", json=payload)

    assert response.status_code == 200, (
        f"Expected 200 from JSONPlaceholder mock, got {response.status_code}. "
        "JSONPlaceholder does not enforce existence checks."
    )
    body = response.json()
    assert isinstance(body, dict), "Response body should be a JSON object"


def test_patch_post_edge_case_empty_body():
    """
    Send a PATCH request with an empty body to an existing post (ID 1);
    API should return 200 with no changes applied.
    """
    post_id = 1
    response = requests.patch(f"{BASE_URL}/posts/{post_id}", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == post_id, f"Returned post id should still be {post_id}"
    # Original fields should remain intact
    assert "title" in body, "Post object should still contain 'title'"
    assert "userId" in body, "Post object should still contain 'userId'"


# ---------------------------------------------------------------------------
# DELETE /posts/{id}
# ---------------------------------------------------------------------------

def test_delete_post_happy_path():
    """
    Delete an existing post by valid ID (1) and verify a 200 response
    with an empty object.
    """
    post_id = 1
    response = requests.delete(f"{BASE_URL}/posts/{post_id}")

    assert response.status_code == 200
    body = response.json()
    # JSONPlaceholder returns {} on successful delete
    assert isinstance(body, dict), "DELETE response body should be a JSON object"
    assert body == {}, "DELETE response body should be an empty object"


def test_delete_post_not_found():
    """
    Attempt to delete a post with a non-existent ID (99999);
    JSONPlaceholder returns 200 for DELETE on non-existent IDs.
    """
    response = requests.delete(f"{BASE_URL}/posts/99999")

    assert response.status_code == 200, (
        f"Expected 200 from JSONPlaceholder mock, got {response.status_code}. "
        "JSONPlaceholder does not enforce existence checks."
    )
    body = response.json()
    assert isinstance(body, dict), "Response body should be a JSON object"
