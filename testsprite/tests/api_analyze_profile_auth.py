import requests

BASE_URL = "https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com"


def test_analyze_profile_requires_auth():
    response = requests.post(
        f"{BASE_URL}/api/analyze-profile",
        json={
            "skill": "Python",
            "goal": "build projects",
            "level": "none",
            "time": "1 hour per day",
        },
        timeout=30,
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert "error" in data
