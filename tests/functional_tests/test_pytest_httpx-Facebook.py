import pytest
import httpx
from pytest_httpx import HTTPXMock
import json

# This is a sample function that would perform the OAuth2 flow for Facebook.
# Made it synchronous for simplicity in this test.
def get_user_info_from_facebook(auth_code: str):
    """
    Simulates a function that exchanges an authorization code for an
    access token and then uses that token to get user info from Facebook.
    """
    client = httpx.Client()

    # --- Step 1: Exchange auth code for token ---
    # This is the "ping" to the Facebook token endpoint.
    # Note: Using the latest Graph API version (e.g., v19.0)
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    token_payload = {
        "code": auth_code,
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "redirect_uri": "http://localhost",
    }

    # Facebook's token endpoint expects application/x-www-form-urlencoded data,
    # so we use the 'data' parameter in the post request.
    token_response = client.post(token_url, data=token_payload)

    token_response.raise_for_status()
    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise ValueError("Access token not found in response.")

    # --- Step 2: Use access token to get user info ---
    # This is the next "ping" to the Facebook user profile endpoint.
    # We explicitly request the fields we need.
    userinfo_url = f"https://graph.facebook.com/v19.0/me?fields=id,name,email"
    headers = {"Authorization": f"Bearer {access_token}"}

    # The final "pong" is the user info data.
    userinfo_response = client.get(userinfo_url, headers=headers)
    userinfo_response.raise_for_status()
    return userinfo_response.json()


# --- The actual test using pytest-httpx ---
# The httpx_mock fixture is provided by pytest-httpx.
def test_facebook_oauth2_flow(httpx_mock: HTTPXMock):
    """
    Tests a complete Facebook OAuth2 flow by mocking the responses
    for both the token and user info endpoints.
    """
    # Define the mock responses in the order they will be received.

    # --- Mock Response for the Token Endpoint (Pong 1) ---
    httpx_mock.add_response(
        url="https://graph.facebook.com/v19.0/oauth/access_token",
        method="POST",
        status_code=200,
        json={
            "access_token": "mocked_facebook_access_token",
            "token_type": "bearer",
            "expires_in": 5183999,
        },
    )

    # --- Mock Response for the User Info Endpoint (Pong 2) ---
    # We need to match the URL exactly, including the fields query.
    httpx_mock.add_response(
        url="https://graph.facebook.com/v19.0/me?fields=id,name,email",
        method="GET",
        status_code=200,
        json={
            "id": "1234567890",
            "name": "Test User",
            "email": "testuser@example.com",
        },
    )

    # Call the function we want to test.
    # It will make the two HTTP requests sequentially.
    user_data = get_user_info_from_facebook(auth_code="mock_auth_code")

    # --- Assertions to verify the test worked correctly ---
    assert user_data is not None
    assert user_data["name"] == "Test User"
    assert user_data["email"] == "testuser@example.com"
    
    # Check if the mocked calls were made correctly.
    requests = httpx_mock.get_requests()
    assert len(requests) == 2

    # Verify the first request (token exchange)
    assert requests[0].url == "https://graph.facebook.com/v19.0/oauth/access_token"
    # Facebook's API expects the payload to be form-encoded.
    assert "code=mock_auth_code" in requests[0].content.decode("utf-8")

    # Verify the second request (user info)
    assert requests[1].url == "https://graph.facebook.com/v19.0/me?fields=id,name,email"
    assert "mocked_facebook_access_token" in requests[1].headers["Authorization"]
