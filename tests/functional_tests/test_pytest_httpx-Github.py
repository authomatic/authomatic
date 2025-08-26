import pytest
import httpx
from pytest_httpx import HTTPXMock
import json

# This is a function that would perform the OAuth2 flow for GitHub.
# Made it synchronous for simplicity in this test.
def get_user_info_from_github(auth_code: str):
    """
    Simulates a function that exchanges an authorization code for an
    access token and then uses that token to get user info from GitHub.
    """
    client = httpx.Client()

    # --- Step 1: Exchange auth code for token ---
    # This is the "ping" to the GitHub token endpoint.
    token_url = "https://github.com/login/oauth/access_token"
    token_payload = {
        "code": auth_code,
        "client_id": "Ov23liWHsnFgT3XWVFrp",
        "client_secret": "8def4ea2d890875e87cd130a7cea6ad1951f1ff6",
        "redirect_uri": "http://localhost",
    }

    # GitHub's token endpoint can return form-encoded or JSON. We request JSON
    # explicitly with the 'Accept' header to make parsing easier.
    headers = {"Accept": "application/json"}
    token_response = client.post(token_url, json=token_payload, headers=headers)

    token_response.raise_for_status()
    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise ValueError("Access token not found in response.")

    # --- Step 2: Use access token to get user info ---
    # This is the next "ping" to the GitHub user profile endpoint.
    userinfo_url = "https://api.github.com/user"
    headers = {"Authorization": f"token {access_token}"}

    # The final "pong" is the user info data.
    userinfo_response = client.get(userinfo_url, headers=headers)
    userinfo_response.raise_for_status()
    return userinfo_response.json()


# --- The actual test using pytest-httpx ---
# The httpx_mock fixture is provided by pytest-httpx.
def test_github_oauth2_flow(httpx_mock: HTTPXMock):
    """
    Tests a complete GitHub OAuth2 flow by mocking the responses
    for both the token and user info endpoints.
    """
    # Define the mock responses in the order they will be received.

    # --- Mock Response for the Token Endpoint (Pong 1) ---
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        method="POST",
        status_code=200,
        json={
            "access_token": "mocked_github_access_token",
            "scope": "user",
            "token_type": "bearer",
        },
    )

    # --- Mock Response for the User Info Endpoint (Pong 2) ---
    httpx_mock.add_response(
        url="https://api.github.com/user",
        method="GET",
        status_code=200,
        json={
            "login": "testuser_gh",
            "id": 1234567,
            "node_id": "MDEyOk9yZ2FuaXphdGlvbjM4OTA4MzI5",
            "avatar_url": "https://avatars.githubusercontent.com/u/1234567?v=4",
            "name": "Test User",
            "company": "GitHub Inc.",
            "public_repos": 10,
        },
    )

    # Call the function we want to test.
    # It will make the two HTTP requests sequentially.
    user_data = get_user_info_from_github(auth_code="mock_auth_code")

    # --- Assertions to verify the test worked correctly ---
    assert user_data is not None
    assert user_data["login"] == "testuser_gh"
    assert user_data["public_repos"] == 10
    
    # check if the mocked calls were made correctly.
    requests = httpx_mock.get_requests()
    assert len(requests) == 2

    # Verify the first request (token exchange)
    assert requests[0].url == "https://github.com/login/oauth/access_token"
    # GitHub's API expects the payload to be JSON if the 'Accept' header is set to 'application/json'
    assert json.loads(requests[0].content)["code"] == "mock_auth_code"

    # Verify the second request (user info)
    assert requests[1].url == "https://api.github.com/user"
    assert "mocked_github_access_token" in requests[1].headers["Authorization"]

