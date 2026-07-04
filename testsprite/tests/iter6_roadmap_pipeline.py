import requests

BASE_URL = "https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com"
TEST_EMAIL = "k.erden03@gmail.com"
TEST_PASSWORD = "123456"
PROJECT_ICONS = {"🚀", "💻", "🎮", "📊", "🌐", "🤖", "📱", "🎨"}


def _get_token():
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["token"]


def test_analyze_profile_returns_youtube_roadmap_with_project_card():
    token = _get_token()
    response = requests.post(
        f"{BASE_URL}/api/analyze-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "skill": "SQL",
            "goal": "query databases",
            "level": "basic",
            "time": "2 weeks",
        },
        timeout=180,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("success") is True
    assert data.get("roadmap_title")
    assert data.get("total_steps") == len(data.get("roadmap_steps") or [])

    steps = data.get("roadmap_steps") or []
    assert len(steps) >= 2, "roadmap needs video steps plus project card"

    first = steps[0]
    for field in ("id", "title", "description", "link", "status", "icon"):
        assert field in first, f"missing {field} in first step"

    assert first["icon"] == "🎬"
    assert first["status"] == "current"

    for step in steps[:-1]:
        assert step["icon"] == "🎬", f"video step expected 🎬, got {step.get('icon')}"

    last = steps[-1]
    assert last["icon"] in PROJECT_ICONS, f"project icon expected, got {last.get('icon')}"
    assert last["status"] == "locked"
    assert last["link"] == "#"
