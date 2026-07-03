# KnowledgeWar — LOOP.md

> **Agent-written verification log.** Write → Verify → Fix → Verify.  
> **Maker:** Cursor · **Checker:** TestSprite CLI  
> **Project:** `1839c68e-2f6e-497e-a25f-7c9b798a7c1a`

---

### Baseline

> _Why:_ Ship the app live and bank an initial TestSprite suite as a reference point.

| # | Action | TestSprite | Result |
|---|--------|-----------|--------|
| 1 | Deployed KnowledgeWar to Render (free tier) | — | Live at https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com |
| 2 | Created TestSprite project `50dc7e80` | — | Frontend project, target URL set |
| 3 | Created "KnowledgeWar Login Flow" suite (7 UI tests) | Integration Tests | Initial run: **3 PASSED / 2 FAILED / 2 BLOCKED** |
| 4 | Production prep: gunicorn, `SECRET_KEY` from env, Procfile, `.env.example` | — | Render deploy **PASSED** |
| 5 | CI/CD: `.github/workflows/testsprite.yml` + `TESTSPRITE_TOKEN` secret | — | Workflow ready |

---

### Iteration 1 — CI/CD + CLI Setup

> _Why:_ Automate test runs on every push so regressions are caught early.

| # | Action | TestSprite | Result |
|---|--------|-----------|--------|
| 6 | CLI setup (`testsprite setup --from-env`); project listed | CLI | **PASSED** |
| 7 | Discovered: `test run --all --project` skips FE tests (BE-only batch) | CLI | **SKIPPED** — run FE tests individually by ID |
| 8 | **FIX:** Workflow — Node 20, npm CLI, wake live URL before run | `.github/workflows/testsprite.yml` | Committed |
| 9 | **FIX:** `seed_default_test_user()` — `k.erden03@gmail.com` / `123456` on every deploy | `app.py` | Render ephemeral SQLite; user recreated each deploy |
| 10 | TestSprite portal: Authentication + live URL configured | Portal | Login flow **PASSED** |

---

### Iteration 2 — Fresh start: new project + 6 FE guest/auth tests — `1839c68e`

> _Why:_ Rebuilt the suite from scratch on a new TestSprite project, focused on the guest experience (landing, nav, i18n, login/register, logout) after removing the home "Tournaments" nav link.

| # | Action | TestSprite | Result |
|---|--------|-----------|--------|
| 11 | **FIX:** Removed `#tournaments` nav link from home (guests can't see tournaments) | `templates/index.html` | Committed |
| 12 | Deleted old FE suite + project; created new project `1839c68e` (portal, no test-account so guest tests stay guest) | Portal | New project ready |
| 13 | Authored 6 new FE plans in `testsprite-plans/` | CLI `create-batch` | **6 created / 0 failed** |
| 14 | Repointed 6 plans + docs to new `projectId`; wired 6 IDs into CI | `testsprite-plans/*`, `.github/workflows/testsprite.yml` | Committed |
| 15 | GitHub Actions on push (auto `push` + `workflow_dispatch`) | Actions | **4 PASS / 2 BLOCKED** |
| 16 | Pulled blocked bundles — both are false-blocked (agent wrote a summary instead of a formal PASS) | `artifact get` | `79e02413` (02), `9cf8ac1e` (06) |

#### Frontend results — GitHub Actions 

| Verdict | Test ID | Name | Purpose |
|---------|---------|------|---------|
| **PASS** | `5d9b778f` | Home hero content + EN\|TR toggle | Hero ('AI-POWERED', 'LEARNING PLATFORM', 'personalized roadmap') and EN\|TR toggle render |
| **BLOCKED** | `9d591c13` | Home nav anchor scroll | Home / How it works / Features links scroll to their sections (false blocked — nav works) |
| **PASS** | `acaa43a5` | Home i18n TR | Turkish toggle shows 'Anasayfa', 'Nasıl Çalışır', 'Özellikler', 'Giriş Yap' |
| **PASS** | `d6999073` | Guest nav | Guest sees only Home / How it works / Features + Log in / Sign up; no Tournaments/Profile |
| **PASS** | `88d22a64` | Login / Register form (EN) | Login ('Welcome back') and register ('Join the journey', 'Create account') forms render |
| **BLOCKED** | `bac70c37` | Logout flow | Login then logout restores guest view + 'Log in' button (false blocked — logout works) |

**Score: 4 PASS / 2 BLOCKED** — both blocked are false positives; app behavior verified in the failure bundles. CI exit 1 because `testsprite test run` treats BLOCKED as non-zero.

#### Waived — false blocked (app works, not a bug)

| Test ID | Name | Purpose | Reason |
|---------|------|---------|--------|
| `9d591c13` | Home nav anchor scroll | Nav links scroll to sections | Agent summary: "All requested navigation checks completed successfully" — verdict box got a summary instead of a formal PASS |
| `bac70c37` | Logout flow | Logout restores guest view | Agent summary: "Test outcome: PASS (success=true)" — same verdict-format issue |

> _Lesson for next plans:_ keep the **final assertion single and concrete** (one observable element/text). Multi-part or narrative last steps make the agent write a summary and the run ends up **BLOCKED** instead of PASS.

---

<!-- ŞABLON: Yeni iterasyonları aşağıdaki şema (sütun yapısı) ile ekleyin. Testler yapılacak.txt'ten seçilecek. -->

### Iteration N — <title>

> _Why:_ <reason>

| # | Action | TestSprite | Result |
|---|--------|-----------|--------|
|   |        |           |        |

#### Frontend results (schema)

| Verdict | Test ID | Name | Purpose |
|---------|---------|------|---------|
|         |         |      |         |

#### Backend (schema)

| Test ID | Name | Status | Purpose |
|---------|------|--------|---------|
|         |      |        |         |

#### Waived (schema)

| Test ID | Name | Purpose | Reason |
|---------|------|---------|--------|
|         |      |         |        |

---

## Summary

| Metric | Count |
|--------|:---:|
| Current project | `1839c68e` |
| FE tests (step 1 suite) | **6** |
| Last CI run (2026-07-03) | **4 PASS / 2 BLOCKED** (both waived) |
| Banked (PASS) | `5d9b778f`, `acaa43a5`, `d6999073`, `88d22a64` |
| Waived (false blocked) | `9d591c13`, `bac70c37` |
| Backend tests | Not yet recreated on new project |
| CI on push | Enabled (`push` to master + `workflow_dispatch`) |

**Evidence:** https://github.com/Kerden22/TestSprite_HackathonSeason3_KnowledgeWar/commits/master  
**Live URL:** https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com  
**TestSprite Dashboard:** https://www.testsprite.com/dashboard/tests/1839c68e-2f6e-497e-a25f-7c9b798a7c1a
