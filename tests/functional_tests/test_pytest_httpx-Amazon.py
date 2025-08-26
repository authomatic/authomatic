import pytest
import httpx
from pytest_httpx import HTTPXMock
import json

# This is a function that would perform the OAuth2 flow for Amazon.
# Made it synchronous for simplicity in this test.
def get_user_info_from_provider(auth_code: str):
    """
    Simulates a function that exchanges an authorization code for an
    access token and then uses that token to get user info from Amazon.
    """
    client = httpx.Client()

    # --- Step 1: Exchange auth code for token ---
    # This is the "ping" to the Amazon token endpoint.
    token_url = "https://api.amazon.com/auth/o2/token"
    token_payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": "amzn1.application-oa2-client.60de1a02255d4792910699f7ba5a3d76",
        "client_secret": "495857d85ebb163d1ca8e57e8b64674dd9ffddb4814f3a7121ec4e75eeff0a5e",
        "redirect_uri": "https://localhost",
    }

    # Use the 'data' parameter for form-encoded bodies as required by Amazon's API.
    token_response = client.post(token_url, data=token_payload)

    token_response.raise_for_status()
    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise ValueError("Access token not found in response.")

    # --- Step 2: Use access token to get user info ---
    # This is the next "ping" to the Amazon user profile endpoint.
    userinfo_url = "https://api.amazon.com/user/profile"
    headers = {"Authorization": f"Bearer {access_token}"}

    # The final "pong" is the user info data.
    userinfo_response = client.get(userinfo_url, headers=headers)
    userinfo_response.raise_for_status()
    return userinfo_response.json()


# --- The actual test using pytest-httpx ---
# The httpx_mock fixture is provided by pytest-httpx.
def test_amazon_oauth2_flow(httpx_mock: HTTPXMock):
    """
    Tests a complete Amazon OAuth2 flow by mocking the responses
    for both the token and userinfo endpoints.
    """
    # Define the mock responses in the order they will be received.

    # --- Mock Response for the Token Endpoint (Pong 1) ---
    httpx_mock.add_response(
        url="https://api.amazon.com/auth/o2/token",
        method="POST",
        status_code=200,
        json={
            "access_token": "mocked_amazon_access_token",
            "refresh_token": "mocked_amazon_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "scope": "profile postal_code",
        },
    )

    # --- Mock Response for the User Info Endpoint (Pong 2) ---
    httpx_mock.add_response(
        url="https://api.amazon.com/user/profile",
        method="GET",
        status_code=200,
        json={
            "user_id": "amzn1.account.AEI6U34NEXQ4",
            "email": "gnuamua@gmail.com",
            "name": "Andrew Himelstieb",
            "postal_code": "81427",
        },
    )

    # Now, we call the function we want to test.
    # It will make the two HTTP requests sequentially.
    # The httpx_mock fixture will intercept them and return our mocked responses.
    user_data = get_user_info_from_provider(auth_code="mock_auth_code_xyz")

    # --- Assertions to verify the test worked correctly ---
    assert user_data is not None
    assert user_data["email"] == "gnuamua@gmail.com"
    assert user_data["name"] == "Andrew Himelstieb"
    assert user_data["postal_code"] == "81427"

    # Optional: You can check if the mocked calls were made correctly.
    requests = httpx_mock.get_requests()
    assert len(requests) == 2

    # Verify the first request (token exchange)
    assert requests[0].url == "https://api.amazon.com/auth/o2/token"
    # Note: Amazon's API expects form-encoded data, not JSON.
    assert "code=mock_auth_code_xyz" in requests[0].content.decode("utf-8")

    # Verify the second request (user info)
    assert requests[1].url == "https://api.amazon.com/user/profile"
    assert "mocked_amazon_access_token" in requests[1].headers["Authorization"]

