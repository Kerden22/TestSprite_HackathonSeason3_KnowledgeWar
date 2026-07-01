# KnowledgeWar — LOOP.md

> **Agent-written verification log.** Write → Verify → Fix → Verify.  
> **Maker:** Cursor · **Checker:** TestSprite CLI  
> **Project:** KnowledgeWar (Bilgi Savaşı) — TestSprite Hackathon Season 3

---

### Baseline — Jun 28 (Render Deploy + Production Prep)

| # | Action | TestSprite | Result |
|---|--------|-----------|--------|
| 1 | Removed RAG/chatbot; slimmed requirements for deploy | — | App starts without mypdf.pdf |
| 2 | Deployed to Render (free tier) | — | Live at https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com |
| 3 | User added gunicorn to requirements.txt; first deploy failed (`gunicorn: command not found`) | — | **FAILED** |
| 4 | **FIX:** gunicorn in requirements + Start Command `gunicorn app:app` | `requirements.txt` | Render redeploy **PASSED** — service live |
| 5 | **FIX:** `script.js` API_BASE_URL localhost → `/api` | `static/script.js:76` | Login/register works on live URL |
| 6 | **FIX:** `SECRET_KEY` from env; production `app.run` (PORT, debug=False) | `app.py:37,2981-2983` | Production-ready |
| 7 | Added Procfile, runtime.txt, README with live URL | — | Deploy config complete |
| 8 | Awaiting TestSprite baseline tests on live URL | — | Pending |

---

## Summary

| Metric | Count |
|--------|:---:|
| Total iterations | 0 (feature loop not started) |
| FAIL → FIX cycles | 1 (gunicorn missing) |
| Tests created | 0 |
| Tests banked (green) | 0 |
| TestSprite reruns | 0 |
| Live URL | https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com |
| GitHub Repo | https://github.com/Kerden22/TestSprite_HackathonSeason3_KnowledgeWar |
