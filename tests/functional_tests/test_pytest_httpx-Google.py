import pytest
import httpx
from pytest_httpx import HTTPXMock
import json

# This is a function that would perform the OAuth2 flow for Google.
# Made it synchronous for simplicity in this test.
def get_user_info_from_google(auth_code: str):
    """
    Simulates a function that exchanges an authorization code for an
    access token and then uses that token to get user info.
    """
    client = httpx.Client()
    
    # --- Step 1: Exchange auth code for token ---
    # This is the "ping" to the token endpoint.
    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "code": auth_code,
        "client_id": "CLIENT_ID",
        "client_secret": "CLIENT_SECRET",
        "redirect_uri": "https://localhost",
        "grant_type": "authorization_code",
    }
    
    # The response is the "pong" from the token endpoint.
    token_response = client.post(token_url, json=token_payload)
    token_response.raise_for_status()
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        raise ValueError("Access token not found in response.")
    
    # --- Step 2: Use access token to get user info ---
    # This is the next "ping" to the userinfo endpoint.
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # The final "pong" is the user info data.
    userinfo_response = client.get(userinfo_url, headers=headers)
    userinfo_response.raise_for_status()
    return userinfo_response.json()


# --- The actual test using pytest-httpx ---
# The httpx_mock fixture is provided by pytest-httpx.
def test_google_oauth2_flow(httpx_mock: HTTPXMock):
    """
    Tests a complete Google OAuth2 flow by mocking the responses
    for both the token and userinfo endpoints.
    """
    # Define the mock responses in the order they will be received.
    
    # --- Mock Response for the Token Endpoint (Pong 1) ---
    # We add this response first because the function will call this endpoint first.
    httpx_mock.add_response(
        url="https://oauth2.googleapis.com/token",
        method="POST",
        status_code=200,
        json={
            "access_token": "mocked_access_token_12345",
            "expires_in": 3600,
            "scope": "https://www.googleapis.com/auth/userinfo.profile",
            "token_type": "Bearer",
        },
    )
    
    # --- Mock Response for the User Info Endpoint (Pong 2) ---
    # This response is added second because it will be the second request.
    httpx_mock.add_response(
        url="https://www.googleapis.com/oauth2/v2/userinfo",
        method="GET",
        status_code=200,
        json={
            "id": "1234567890",
            "email": "gnuamua@gmail.com",
            "verified_email": True,
#            "name": "Test User",
#            "given_name": "Test",
#            "family_name": "User",
        },
    )
    
    # Now, we call the function we want to test.
    # It will make the two HTTP requests sequentially.
    # The httpx_mock fixture will intercept them and return our mocked responses.
    user_data = get_user_info_from_google(auth_code="mock_auth_code_xyz")
    
    # --- Assertions to verify the test worked correctly ---
    assert user_data is not None
    assert user_data["email"] == "gnuamua@gmail.com"
#    assert user_data["name"] == "Test User"
    
    # Optional: You can check if the mocked calls were made correctly.
    # The httpx_mock.get_requests() method returns all the intercepted requests.
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    
    # Verify the first request (token exchange)
    assert requests[0].url == "https://oauth2.googleapis.com/token"
    assert json.loads(requests[0].content)["code"] == "mock_auth_code_xyz"
    
    # Verify the second request (user info)
    assert requests[1].url == "https://www.googleapis.com/oauth2/v2/userinfo"
    assert "mocked_access_token_12345" in requests[1].headers["Authorization"]

# To run this test:
# 1. Make sure you have pytest and pytest-httpx installed:
#    pip install pytest pytest-httpx httpx
# 2. Save the code as a Python file (e.g., test_oauth.py).
# 3. Run the test from your terminal:
#    pytest test_oauth.py


