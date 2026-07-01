# TestSprite Suite — KnowledgeWar

**Project:** `50dc7e80-8d2d-4933-8c55-5361fab9ebb2`  
**Live URL:** https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com  
**Test user:** `k.erden03@gmail.com` / `123456`

## Frontend (25 tests)

### Existing — auth & home (7)

| ID | Plan file | Name |
|----|-----------|------|
| `b14b87e9-...` | `.testsprite/plans/b14b87e9-home-content.json` | Home hero content |
| `73374ea0-...` | `.testsprite/plans/73374ea0-guest-nav.json` | Guest nav |
| `28118134-...` | `.testsprite/plans/28118134-guest-primary-nav.json` | Guest nav + Home |
| `c3f060b1-...` | `.testsprite/plans/c3f060b1-login-tournament.json` | Login → tournament |
| `ad90b2b9-...` | `.testsprite/plans/ad90b2b9-login-tournament-repeat.json` | Tournament repeat |
| `d747883b-...` | `.testsprite/plans/d747883b-features-anchor.json` | Features anchor |
| `d32cca15-...` | `.testsprite/plans/d32cca15-features-repeat.json` | Features repeat |

### New — i18n & pages (18)

| ID | Plan file | Name |
|----|-----------|------|
| `1064d65e-...` | `testsprite-plans/01-home-i18n-tr.json` | Home TR |
| `cd17f8ca-...` | `testsprite-plans/02-home-i18n-en.json` | Home EN |
| `2fe15023-...` | `testsprite-plans/03-login-i18n-tr.json` | Login TR |
| `e6d48742-...` | `testsprite-plans/04-roadmap-i18n-tr.json` | Roadmap TR |
| `54a8c006-...` | `testsprite-plans/05-learn-i18n-tr.json` | Learn TR |
| `62968e6e-...` | `testsprite-plans/06-test-i18n-tr.json` | Test TR |
| `ed7b621c-...` | `testsprite-plans/07-tournament-i18n-tr.json` | Tournament TR |
| `98fc7986-...` | `testsprite-plans/08-profile-i18n-tr.json` | Profile TR |
| `925fd7eb-...` | `testsprite-plans/09-roadmap-smoke-en.json` | Roadmap EN |
| `db296a54-...` | `testsprite-plans/10-learn-smoke-en.json` | Learn EN |
| `cafbbc5c-...` | `testsprite-plans/11-test-smoke-en.json` | Test EN |
| `359739b2-...` | `testsprite-plans/12-profile-smoke-en.json` | Profile EN |
| `5cf8b6d4-...` | `testsprite-plans/13-login-register-en.json` | Register form |
| `4a6a7cf9-...` | `testsprite-plans/14-cross-page-nav.json` | Cross-page nav |
| `dc6769f8-...` | `testsprite-plans/15-guest-profile-redirect.json` | Guest → profile |
| `a5b1c09f-...` | `testsprite-plans/16-guest-tournament-redirect.json` | Guest → tournament |
| `c2d5d7c3-...` | `testsprite-plans/17-logged-in-home-nav.json` | Logged-in nav |
| `302da8b4-...` | `testsprite-plans/18-logout-flow.json` | Logout |

## Backend (5 tests)

| ID | File |
|----|------|
| `822308eb-...` | `testsprite/tests/api_login.py` |
| `85b52f13-...` | `testsprite/tests/api_profile_auth.py` |
| `d1753dd2-...` | `testsprite/tests/api_tournaments.py` |
| `31e5401a-...` | `testsprite/tests/api_active_course.py` |
| `3d145644-...` | `testsprite/tests/api_completed_courses.py` |

## CI

- **Push:** all 25 FE tests (`.github/workflows/testsprite.yml`)
- **Manual dispatch + `run_backend=true`:** 5 BE tests

## Commands

```bash
testsprite setup --from-env
testsprite test create-batch --plan-from-dir ./testsprite-plans
testsprite test run <testId> --wait
```
