# KnowledgeWar — LOOP.md

> **Agent-written verification log.** Write → Verify → Fix → Verify.  
> **Maker:** Cursor · **Checker:** TestSprite CLI  
> **Project:** `50dc7e80-8d2d-4933-8c55-5361fab9ebb2`

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
|        |     |

**Evidence:** https://github.com/Kerden22/TestSprite_HackathonSeason3_KnowledgeWar/commits/master  
**Live URL:** https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com  
**TestSprite Dashboard:** https://www.testsprite.com/dashboard/tests/50dc7e80-8d2d-4933-8c55-5361fab9ebb2
