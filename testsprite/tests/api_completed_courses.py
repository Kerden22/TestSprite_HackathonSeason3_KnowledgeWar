import os
import requests

BASE_URL = "https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com"
TEST_EMAIL = "k.erden03@gmail.com"
TEST_PASSWORD = "123456"


def _get_token():
    token = os.environ.get("AUTH_TOKEN")
    if token:
        return token
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["token"]


def test_completed_courses_with_auth():
    token = _get_token()
    response = requests.get(
        f"{BASE_URL}/api/completed-courses",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "completed_courses" in data
    assert isinstance(data["completed_courses"], list)
