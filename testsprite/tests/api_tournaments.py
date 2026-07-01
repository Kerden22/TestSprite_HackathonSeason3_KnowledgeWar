import requests

BASE_URL = "https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com"


def test_tournaments_list():
    response = requests.get(f"{BASE_URL}/api/tournaments", timeout=30)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "tournaments" in data
    assert isinstance(data["tournaments"], list)
