import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /comments  (no filter)
# ---------------------------------------------------------------------------

def test_get_comments_happy_path():
    """
    Retrieve all comments without any filter and verify a 200 response
    with an array of comment objects.
    """
    response = requests.get(f"{BASE_URL}/comments")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list), "Response body should be a list"
    assert len(body) > 0, "Comments list should not be empty"
    first_comment = body[0]
    assert "id" in first_comment, "Comment object should contain 'id'"
    assert "postId" in first_comment, "Comment object should contain 'postId'"
    assert "name" in first_comment, "Comment object should contain 'name'"
    assert "email" in first_comment, "Comment object should contain 'email'"
    assert "body" in first_comment, "Comment object should contain 'body'"


# ---------------------------------------------------------------------------
# GET /comments?postId=1  (filter by valid postId)
# ---------------------------------------------------------------------------

def test_get_comments_by_postid_happy_path():
    """
    Retrieve comments filtered by a valid postId (1) and verify a 200 response
    with only comments belonging to that post.
    """
    post_id = 1
    response = requests.get(f"{BASE_URL}/comments", params={"postId": post_id})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list), "Response body should be a list"
    assert len(body) > 0, f"There should be comments for postId={post_id}"
    for comment in body:
        assert comment["postId"] == post_id, (
            f"Every returned comment should have postId={post_id}, "
            f"but got postId={comment['postId']}"
        )
    # Verify comment structure
    assert "id" in body[0], "Comment object should contain 'id'"
    assert "email" in body[0], "Comment object should contain 'email'"


# ---------------------------------------------------------------------------
# GET /comments?postId=99999  (non-existent postId -> empty array)
# ---------------------------------------------------------------------------

def test_get_comments_not_found_postid():
    """
    Retrieve comments filtered by a non-existent postId (99999);
    expect a 200 response with an empty array.
    """
    response = requests.get(f"{BASE_URL}/comments", params={"postId": 99999})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list), "Response body should be a list"
    assert body == [], "No comments should be returned for a non-existent postId"


# ---------------------------------------------------------------------------
# GET /comments?postId=invalid  (non-integer postId)
# ---------------------------------------------------------------------------

def test_get_comments_invalid_input_non_integer_postid():
    """
    Retrieve comments with a non-integer postId query parameter (string value);
    JSONPlaceholder does not enforce type validation on query parameters
    and will return 200 with an empty list.
    """
    response = requests.get(f"{BASE_URL}/comments", params={"postId": "invalid"})

    assert response.status_code == 200, (
        f"Expected 200 from JSONPlaceholder mock, got {response.status_code}. "
        "JSONPlaceholder does not enforce type validation."
    )
    body = response.json()
    assert body is not None, "Response body should not be None"
    assert body == [], "JSONPlaceholder should return an empty list for a non-integer postId"


# ---------------------------------------------------------------------------
# GET /comments?postId=0  (boundary below valid range)
# ---------------------------------------------------------------------------

def test_get_comments_edge_case_postid_zero():
    """
    Retrieve comments with postId set to 0 (boundary below valid range);
    expect a 200 with an empty array or a 4xx.

    JSONPlaceholder returns 200 with an empty array for postId=0.
    """
    response = requests.get(f"{BASE_URL}/comments", params={"postId": 0})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list), "Response body should be a list"
    # postId=0 does not correspond to any real post, so the list should be empty
    assert body == [], "No comments should be returned for postId=0"
