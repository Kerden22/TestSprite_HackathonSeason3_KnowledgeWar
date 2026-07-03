# TestSprite Suite — KnowledgeWar

**Project:** `1839c68e-2f6e-497e-a25f-7c9b798a7c1a`  
**Live URL:** https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com  
**Test user:** `k.erden03@gmail.com` / `123456`

## Frontend — Iteration 2 (6 tests)

| ID | Plan file | Name | CI |
|----|-----------|------|----|
| `5d9b778f-...` | `testsprite-plans/01-home-content.json` | Home hero content + EN\|TR toggle | yes |
| `9d591c13-...` | `testsprite-plans/02-home-nav-anchor.json` | Home nav anchor scroll | waived (false blocked) |
| `acaa43a5-...` | `testsprite-plans/03-home-i18n-tr.json` | Home i18n TR | yes |
| `d6999073-...` | `testsprite-plans/04-guest-nav.json` | Guest nav | yes |
| `88d22a64-...` | `testsprite-plans/05-login-register-form.json` | Login / Register form EN | yes |
| `bac70c37-...` | `testsprite-plans/06-logout-flow.json` | Logout flow | waived (false blocked) |

## Frontend — Iteration 3 (6 tests, auth gates + logged-in)

| ID | Plan file | Name | CI |
|----|-----------|------|----|
| `bebca88c-...` | `testsprite-plans/07-guest-tournament-redirect.json` | Guest -> /tournament redirects to /login | yes |
| `3053ece4-...` | `testsprite-plans/08-guest-profile-redirect.json` | Guest -> /profile redirects to /login | yes |
| `fe10d08c-...` | `testsprite-plans/09-guest-roadmap-redirect.json` | Guest -> /roadmap redirects to /login | yes |
| `ebe0b04d-...` | `testsprite-plans/10-home-anchor-i18n.json` | Language toggle on hash-anchored URL | yes |
| `f2742156-...` | `testsprite-plans/11-loggedin-home-nav.json` | Logged-in home shows Roadmap + Tournaments | yes |
| `64381628-...` | `testsprite-plans/12-loggedin-tournament-roadmap.json` | Logged-in opens /tournament + /roadmap | yes |

## Backend (5 tests — not yet re-created on new project)

| File | Name |
|------|------|
| `testsprite/tests/api_login.py` | API: login returns token |
| `testsprite/tests/api_profile_auth.py` | API: profile requires auth |
| `testsprite/tests/api_tournaments.py` | API: tournaments list |
| `testsprite/tests/api_active_course.py` | API: active course with auth |
| `testsprite/tests/api_completed_courses.py` | API: completed courses with auth |

## CI

- **Manual:** `.github/workflows/testsprite.yml` (`workflow_dispatch`) — runs all 6 FE tests

## Commands

```bash
testsprite setup --from-env
testsprite test create-batch --plan-from-dir ./testsprite-plans
testsprite test run <testId> --wait
```
