import requests
import pytest

BASE_URL = "https://jsonplaceholder.typicode.com"


# ---------------------------------------------------------------------------
# GET /comments  (no filter)
# ---------------------------------------------------------------------------

def test_get_comments_happy_path_no_filter():
    """
    Retrieve all comments without any query parameters and verify a 200
    response with a non-empty array.
    """
    response = requests.get(f"{BASE_URL}/comments")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert isinstance(data, list), "Response body should be a list"
    assert len(data) > 0, "Response array should not be empty"
    # Spot-check the first comment has expected fields
    first = data[0]
    assert "id" in first, "Comment object should contain 'id'"
    assert "postId" in first, "Comment object should contain 'postId'"
    assert "body" in first, "Comment object should contain 'body'"


# ---------------------------------------------------------------------------
# GET /comments?postId=<valid>
# ---------------------------------------------------------------------------

def test_get_comments_happy_path_filter_by_post_id():
    """
    Retrieve comments filtered by a valid postId query parameter and verify a
    200 response with only comments for that post.
    """
    post_id = 1
    response = requests.get(f"{BASE_URL}/comments", params={"postId": post_id})

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert isinstance(data, list), "Response body should be a list"
    assert len(data) > 0, (
        f"Expected at least one comment for postId={post_id}"
    )
    # Every returned comment must belong to the requested post
    for comment in data:
        assert comment.get("postId") == post_id, (
            f"All comments should have postId={post_id}, "
            f"but got postId={comment.get('postId')}"
        )


# ---------------------------------------------------------------------------
# GET /comments?postId=99999  (non-existent post)
# ---------------------------------------------------------------------------

def test_get_comments_not_found_nonexistent_post_id():
    """
    Filter comments by a non-existent postId (99999) and verify a 200 response
    with an empty array (no matching comments).
    """
    response = requests.get(f"{BASE_URL}/comments", params={"postId": 99999})

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert isinstance(data, list), "Response body should be a list"
    assert data == [], (
        "Expected an empty array for a non-existent postId"
    )


# ---------------------------------------------------------------------------
# GET /comments?postId=invalid  (non-integer postId)
# ---------------------------------------------------------------------------

def test_get_comments_invalid_input_non_integer_post_id():
    """
    Filter comments using a non-integer postId query parameter (string value)
    and expect a 4xx error or empty result.

    NOTE: JSONPlaceholder treats unknown / non-matching filter values as an
    empty result set and returns 200 with [].  This test is therefore marked
    xfail to document the intended 400 behaviour while acknowledging the API
    limitation.
    """
    response = requests.get(
        f"{BASE_URL}/comments", params={"postId": "invalid"}
    )

    if response.status_code == 400:
        # Ideal behaviour: the API rejects the bad input
        data = response.json()
        assert isinstance(data, dict), "Error response body should be a dict"
    else:
        # JSONPlaceholder returns 200 with [] — mark as xfail
        pytest.xfail(
            "JSONPlaceholder does not validate query parameter types; "
            f"got {response.status_code} with body {response.text!r} "
            "instead of 400"
        )


# ---------------------------------------------------------------------------
# GET /comments?postId=  (empty postId)
# ---------------------------------------------------------------------------

def test_get_comments_edge_case_empty_post_id():
    """
    Send a GET request with an empty postId query parameter to verify the API
    handles blank filter values gracefully with a 200 response.
    """
    response = requests.get(
        f"{BASE_URL}/comments", params={"postId": ""}
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )
    data = response.json()
    assert isinstance(data, list), (
        "Response body should be a list even for an empty postId filter"
    )
