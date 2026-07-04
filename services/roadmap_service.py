"""Gemini + YouTube learning roadmap generation."""

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import google.generativeai as genai
import requests

_GEMINI_PLACEHOLDER = "your_gemini_api_key_here"
_genai_configured = False

SUPPORTED_LANGS = ("en", "tr")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def _get_gemini_api_key():
    """Read at call time so load_dotenv() in app.py has already run."""
    return os.getenv("GEMINI_API_KEY", _GEMINI_PLACEHOLDER)


def _get_youtube_api_key():
    return os.getenv("YOUTUBE_API_KEY", "")


def _ensure_genai_configured():
    global _genai_configured
    key = _get_gemini_api_key()
    if key and key != _GEMINI_PLACEHOLDER and not _genai_configured:
        genai.configure(api_key=key)
        _genai_configured = True


def _normalize_lang(lang):
    if not lang:
        return "en"
    normalized = str(lang).lower().strip()
    return normalized if normalized in SUPPORTED_LANGS else "en"


def _strip_json_fences(text):
    response_text = (text or "").strip()
    if not response_text:
        return response_text
    if response_text.startswith("```json"):
        match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        return match.group(1).strip() if match else response_text[7:].strip()
    if response_text.startswith("```"):
        match = re.search(r"```\s*(.*?)\s*```", response_text, re.DOTALL)
        return match.group(1).strip() if match else response_text[3:].strip()
    return response_text


def _clean_and_fix_json(json_text):
    try:
        json.loads(json_text)
        return json_text
    except json.JSONDecodeError:
        if json_text.startswith("```"):
            json_text = re.sub(r"^```(?:json)?\s*", "", json_text)
            json_text = re.sub(r"\s*```$", "", json_text)
        fixed_lines = []
        for line in json_text.split("\n"):
            if '"' in line and line.count('"') % 2 != 0:
                if not line.strip().endswith('"'):
                    line = line.rstrip() + '"'
                if not line.strip().endswith((",", "]", "}")):
                    line = line.rstrip() + ","
            fixed_lines.append(line)
        fixed_text = "\n".join(fixed_lines)
        if not fixed_text.strip().endswith("}"):
            if not fixed_text.strip().endswith("]"):
                fixed_text = fixed_text.rstrip().rstrip(",") + "]"
            if not fixed_text.strip().endswith("}"):
                fixed_text = fixed_text.rstrip().rstrip(",") + "}"
        try:
            json.loads(fixed_text)
            return fixed_text
        except json.JSONDecodeError:
            return '{"steps": []}'


def _demo_gemini_roadmap(skill, goal, level, lang):
    lang = _normalize_lang(lang)
    if lang == "tr":
        title = f"{skill} Öğrenme Yol Haritası"
        steps = [
            {
                "title": f"{skill} Temellerine Giriş",
                "description": f"{skill} nedir ve neden öğrenmelisiniz — hedefiniz: {goal}.",
                "youtube_search_query": f"{skill} tutorial beginner",
            },
            {
                "title": "Temel Kavramlar ve Sözdizimi",
                "description": f"{level} seviyesine uygun temel kavramları öğrenin.",
                "youtube_search_query": f"{skill} basics tutorial",
            },
            {
                "title": "Pratik Uygulamalar",
                "description": "Öğrendiklerinizi küçük örneklerle pekiştirin.",
                "youtube_search_query": f"{skill} practice exercises tutorial",
            },
            {
                "title": "Orta Seviye Konular",
                "description": "Bir sonraki seviyeye geçmek için ileri konulara dalın.",
                "youtube_search_query": f"{skill} intermediate tutorial",
            },
        ]
    else:
        title = f"{skill} Learning Path"
        steps = [
            {
                "title": f"Introduction to {skill}",
                "description": f"What {skill} is and why it matters for your goal: {goal}.",
                "youtube_search_query": f"{skill} tutorial beginner",
            },
            {
                "title": "Core Concepts and Syntax",
                "description": f"Learn fundamentals suited to your {level} level.",
                "youtube_search_query": f"{skill} basics tutorial",
            },
            {
                "title": "Hands-on Practice",
                "description": "Reinforce concepts with small practical examples.",
                "youtube_search_query": f"{skill} practice exercises tutorial",
            },
            {
                "title": "Intermediate Topics",
                "description": "Dive deeper to level up your skills.",
                "youtube_search_query": f"{skill} intermediate tutorial",
            },
        ]
    return {"roadmap_title": title, "steps": steps}


PROJECT_ICONS = ("🚀", "💻", "🎮", "📊", "🌐", "🤖", "📱", "🎨")


def _demo_project_suggestion(skill, lang):
    lang = _normalize_lang(lang)
    if lang == "tr":
        return {
            "title": f"{skill} ile Mini Proje",
            "description": (
                f"{skill} öğrendiklerinizi pekiştirmek için hedefinize uygun "
                "küçük bir proje geliştirin."
            ),
            "icon": "🚀",
        }
    return {
        "title": f"Build a {skill} Mini Project",
        "description": (
            f"Apply what you learned by building a small {skill} project "
            "aligned with your goal."
        ),
        "icon": "🚀",
    }


def generate_project_suggestion(skill, goal, level, lang="en"):
    """Gemini ile son adım proje kartı önerisi."""
    lang = _normalize_lang(lang)
    lang_label = "Turkish" if lang == "tr" else "English"

    if not _get_gemini_api_key() or _get_gemini_api_key() == _GEMINI_PLACEHOLDER:
        print("UYARI: Gemini API anahtarı yok — demo proje önerisi kullanılıyor.")
        return _demo_project_suggestion(skill, lang)

    _ensure_genai_configured()

    prompt = f"""You are a learning coach. Suggest ONE capstone project for a learner.

User inputs:
- skill: {skill}
- goal: {goal}
- level: {level}

Output ONLY valid JSON (no markdown):
{{
  "title": "short project title",
  "description": "2-3 actionable sentences describing what to build",
  "icon": "one emoji from: 🚀 💻 🎮 📊 🌐 🤖 📱 🎨"
}}

Rules:
- Project difficulty must match {level}
- Practical and achievable for the learner's goal
- Write title and description in {lang_label}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        response_text = _clean_and_fix_json(_strip_json_fences(response.text))
        result = json.loads(response_text)
        icon = result.get("icon", "🚀")
        if icon not in PROJECT_ICONS:
            icon = "🚀"
        return {
            "title": (result.get("title") or _demo_project_suggestion(skill, lang)["title"]).strip(),
            "description": (
                result.get("description") or _demo_project_suggestion(skill, lang)["description"]
            ).strip(),
            "icon": icon,
        }
    except Exception as e:
        print(f"Gemini proje önerisi hatası: {e}")
        return _demo_project_suggestion(skill, lang)


def append_project_step(roadmap_steps, skill, goal, level, lang="en"):
    """Video adımlarının sonuna kilitli proje kartı ekle."""
    suggestion = generate_project_suggestion(skill, goal, level, lang)
    roadmap_steps.append(
        {
            "id": len(roadmap_steps) + 1,
            "title": suggestion["title"],
            "description": suggestion["description"],
            "link": "#",
            "video_title": None,
            "thumbnail": None,
            "youtube_search_query": None,
            "status": "locked",
            "icon": suggestion["icon"],
        }
    )
    return roadmap_steps


def generate_roadmap_with_gemini(skill, goal, level, time_commitment, lang="en"):
    """Ask Gemini for a dynamic step-by-step roadmap with YouTube search queries."""
    lang = _normalize_lang(lang)
    lang_label = "Turkish" if lang == "tr" else "English"

    if not _get_gemini_api_key() or _get_gemini_api_key() == _GEMINI_PLACEHOLDER:
        print("UYARI: Gemini API anahtarı yok — demo roadmap kullanılıyor.")
        return _demo_gemini_roadmap(skill, goal, level, lang)

    _ensure_genai_configured()

    prompt = f"""You are a learning path designer. Given user inputs, output ONLY valid JSON (no markdown).

User inputs:
- skill: {skill}
- goal: {goal}
- level: {level}
- time: {time_commitment}

Rules:
- Decide the OPTIMAL number of steps based on skill complexity (e.g. Python 12-15, SQL 5-6). Do NOT use a fixed count.
- Each step MUST have exactly one youtube_search_query (short, specific English keywords for the best tutorial video).
- Steps must progress from fundamentals to advanced topics matching the user's level and goal.
- Write titles and descriptions in {lang_label}.
- Do NOT include a final capstone project step — a separate project card is added later.

Output schema:
{{
  "roadmap_title": "string",
  "steps": [
    {{
      "title": "string",
      "description": "string (1-2 sentences, actionable)",
      "youtube_search_query": "string"
    }}
  ]
}}"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        response_text = _clean_and_fix_json(_strip_json_fences(response.text))
        parsed = json.loads(response_text)
        steps = parsed.get("steps") or []
        if not isinstance(steps, list) or not steps:
            raise ValueError("Gemini returned no steps")
        valid_steps = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            title = (step.get("title") or "").strip()
            description = (step.get("description") or "").strip()
            query = (step.get("youtube_search_query") or "").strip()
            if title and description and query:
                valid_steps.append(
                    {
                        "title": title,
                        "description": description,
                        "youtube_search_query": query,
                    }
                )
        if not valid_steps:
            raise ValueError("No valid steps after parsing")
        return {
            "roadmap_title": (parsed.get("roadmap_title") or f"{skill} Learning Path").strip(),
            "steps": valid_steps,
        }
    except Exception as e:
        err = str(e)
        if "429" in err:
            retry_match = re.search(r"retry in ([\d.]+)s", err, re.IGNORECASE)
            wait = int(float(retry_match.group(1))) + 2 if retry_match else 35
            print(f"Gemini kota aşıldı, {wait}s bekleniyor...")
            time.sleep(wait)
            try:
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                response_text = _clean_and_fix_json(_strip_json_fences(response.text))
                parsed = json.loads(response_text)
                steps = parsed.get("steps") or []
                if steps:
                    return {
                        "roadmap_title": (parsed.get("roadmap_title") or f"{skill} Learning Path").strip(),
                        "steps": steps,
                    }
            except Exception as retry_err:
                print(f"Gemini roadmap retry hatası: {retry_err}")
        print(f"Gemini roadmap hatası: {e}")
        return _demo_gemini_roadmap(skill, goal, level, lang)


def search_youtube_video(query):
    """Fetch the top YouTube video for a search query."""
    youtube_key = _get_youtube_api_key()
    if not youtube_key or not query:
        return None
    try:
        response = requests.get(
            YOUTUBE_SEARCH_URL,
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 1,
                "key": youtube_key,
                "safeSearch": "strict",
                "relevanceLanguage": "en",
            },
            timeout=15,
        )
        if response.status_code != 200:
            print(f"YouTube API hatası ({response.status_code}): {response.text[:200]}")
            return None
        items = response.json().get("items", [])
        if not items:
            print(f"YouTube 0 sonuç: {query!r}")
            return None
        item = items[0]
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            return None
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
        )
        return {
            "video_id": video_id,
            "video_title": snippet.get("title", ""),
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": thumbnail,
        }
    except Exception as e:
        print(f"YouTube arama hatası ({query!r}): {e}")
        return None


def enrich_steps_with_youtube(gemini_steps, max_workers=5):
    """Attach YouTube video metadata to each Gemini step."""
    enriched = []
    video_results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(search_youtube_video, step["youtube_search_query"]): idx
            for idx, step in enumerate(gemini_steps)
        }
        for future in as_completed(futures):
            video_results[futures[future]] = future.result()

    for i, step in enumerate(gemini_steps, 1):
        video = video_results.get(i - 1)
        enriched.append(
            {
                "id": i,
                "title": step["title"],
                "description": step["description"],
                "link": video["video_url"] if video else "#",
                "video_title": video["video_title"] if video else None,
                "thumbnail": video["thumbnail"] if video else None,
                "youtube_search_query": step["youtube_search_query"],
                "status": "current" if i == 1 else "locked",
                "icon": "🎬",
            }
        )
    return enriched


def build_learning_roadmap(skill, goal, level, time_commitment, lang="en"):
    """Full pipeline: Gemini roadmap + YouTube enrichment + capstone project card."""
    gemini_result = generate_roadmap_with_gemini(skill, goal, level, time_commitment, lang)
    roadmap_steps = enrich_steps_with_youtube(gemini_result["steps"])
    append_project_step(roadmap_steps, skill, goal, level, lang)
    return {
        "roadmap_title": gemini_result["roadmap_title"],
        "roadmap_steps": roadmap_steps,
        "total_steps": len(roadmap_steps),
    }
