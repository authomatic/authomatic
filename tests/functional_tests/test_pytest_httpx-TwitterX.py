import pytest
import httpx
from pytest_httpx import HTTPXMock
import json

# This is a function that would perform the OAuth2 flow for Twitter/X.
# Made it synchronous for simplicity in this test.
def get_user_info_from_twitter(auth_code: str, code_verifier: str):
    """
    Simulates a function that exchanges an authorization code for an
    access token and then uses that token to get user info from Twitter/X.
    """
    client = httpx.Client()

    # --- Step 1: Exchange auth code for token ---
    # This is the "ping" to the Twitter/X token endpoint.
    token_url = "https://api.twitter.com/2/oauth2/token"
    token_payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": "https://localhost",
        "client_id": "eG5BY3FNSWFBQUlsN0hOREYwZDg6MTpjaQ",
        "code_verifier": code_verifier,
    }

    # Use the 'data' parameter for form-encoded bodies as required by Twitter/X's API.
    token_response = client.post(token_url, data=token_payload)

    token_response.raise_for_status()
    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise ValueError("Access token not found in response.")

    # --- Step 2: Use access token to get user info ---
    # This is the next "ping" to the Twitter/X user profile endpoint.
    # Note: must specify the fields we want to retrieve.
    userinfo_url = "https://api.twitter.com/2/users/me?user.fields=created_at,description,public_metrics"
    headers = {"Authorization": f"Bearer {access_token}"}

    # The final "pong" is the user info data.
    userinfo_response = client.get(userinfo_url, headers=headers)
    userinfo_response.raise_for_status()
    return userinfo_response.json()


# --- The actual test using pytest-httpx ---
# The httpx_mock fixture is provided by pytest-httpx.
def test_twitter_oauth2_flow(httpx_mock: HTTPXMock):
    """
    Tests a complete Twitter/X OAuth2 flow by mocking the responses
    for both the token and user info endpoints.
    """
    # Define the mock responses in the order they will be received.

    # --- Mock Response for the Token Endpoint (Pong 1) ---
    httpx_mock.add_response(
        url="https://api.twitter.com/2/oauth2/token",
        method="POST",
        status_code=200,
        json={
            "token_type": "bearer",
            "expires_in": 7200,
            "access_token": "mocked_twitter_access_token",
            "scope": "tweet.read users.read",
        },
    )

    # --- Mock Response for the User Info Endpoint (Pong 2) ---
    httpx_mock.add_response(
        url="https://api.twitter.com/2/users/me?user.fields=created_at,description,public_metrics",
        method="GET",
        status_code=200,
        json={
            "data": {
                "id": "123456789",
                "name": "Test User",
                "username": "gnuamua7",
                "created_at": "2018-01-01T00:00:00.000Z",
                "description": "A test account for pytest.",
                "public_metrics": {
                    "followers_count": 100,
                    "following_count": 50,
                    "tweet_count": 20,
                    "listed_count": 5,
                },
            }
        },
    )

    # Now, call the function we want to test.
    # It will make the two HTTP requests sequentially.
    user_data = get_user_info_from_twitter(auth_code="mock_auth_code", code_verifier="mock_code_verifier")

    # --- Assertions to verify the test worked correctly ---
    assert user_data is not None
    assert user_data["data"]["username"] == "gnuamua7"
    assert user_data["data"]["public_metrics"]["followers_count"] == 100
    
    # check if the mocked calls were made correctly.
    requests = httpx_mock.get_requests()
    assert len(requests) == 2

    # Verify the first request (token exchange)
    assert requests[0].url == "https://api.twitter.com/2/oauth2/token"
    assert "code=mock_auth_code" in requests[0].content.decode("utf-8")

    # Verify the second request (user info)
    assert requests[1].url == "https://api.twitter.com/2/users/me?user.fields=created_at,description,public_metrics"
    assert "mocked_twitter_access_token" in requests[1].headers["Authorization"]
