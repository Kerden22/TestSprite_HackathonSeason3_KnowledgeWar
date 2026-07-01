import requests

BASE_URL = "https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com"


def test_profile_requires_auth():
    response = requests.get(f"{BASE_URL}/api/profile", timeout=30)
    assert response.status_code == 401, response.text
    data = response.json()
    assert "error" in data
