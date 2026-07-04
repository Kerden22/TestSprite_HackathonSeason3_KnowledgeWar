import requests

BASE_URL = "https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com"
TEST_EMAIL = "k.erden03@gmail.com"
TEST_PASSWORD = "123456"


def _get_token():
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["token"]


def test_analyze_profile_requires_skill():
    token = _get_token()
    response = requests.post(
        f"{BASE_URL}/api/analyze-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "goal": "build projects",
            "level": "basic",
            "time": "2 hours per week",
        },
        timeout=30,
    )
    assert response.status_code == 400, response.text
    assert "error" in response.json()
