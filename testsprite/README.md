# TestSprite Suite — KnowledgeWar (Iteration 6)

**Project:** `1839c68e-2f6e-497e-a25f-7c9b798a7c1a`  
**Live URL:** https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com  
**Test user:** `k.erden03@gmail.com` / `123456`

## CI on push — 14 tests total (FE → BE)

### Frontend (3)

| ID | Plan | Name |
|----|------|------|
| `a4bd6c04` | `testsprite-plans/23-iter6-learn-smoke.json` | Learn page EN smoke |
| `eca16881` | `testsprite-plans/24-iter6-roadmap-smoke.json` | Roadmap page EN smoke |
| `a4732506` | `testsprite-plans/25-iter6-learn-form.json` | Learn form visible |

### Backend (11)

| ID | File | Name |
|----|------|------|
| `8fe0eb1f` | `api_login.py` | API login returns token |
| `407ed44d` | `api_profile_auth.py` | API profile requires auth |
| `8444706e` | `api_tournaments.py` | API tournaments list |
| `bee6c90f` | `api_active_course.py` | API active course with auth |
| `561cd21f` | `api_completed_courses.py` | API completed courses with auth |
| `70309105` | `iter6_roadmap_auth.py` | Iter6 analyze-profile → 401 |
| `584d61dd` | `iter6_roadmap_validation.py` | Iter6 analyze-profile → 400 |
| `18faba0d` | `api_analyze_profile_auth.py` | Legacy analyze-profile → 401 |
| `36932166` | `api_analyze_profile_validation.py` | Legacy analyze-profile → 400 |
| `a7bbf927` | `api_roadmap_schema.py` | Legacy roadmap schema (Gemini+YouTube) |
| `f046f210` | `iter6_roadmap_pipeline.py` | Iter6 pipeline + project card (Gemini+YouTube) |

**Order:** fast auth/validation first; `a7bbf927` + `f046f210` last (quota).

Requires `GEMINI_API_KEY` + `YOUTUBE_API_KEY` on Render.
