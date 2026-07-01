import requests

BASE_URL = "https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com"
TEST_EMAIL = "k.erden03@gmail.com"
TEST_PASSWORD = "123456"


def test_login_returns_token():
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("success") is True
    assert "token" in data and data["token"]
    assert data.get("user", {}).get("email") == TEST_EMAIL
