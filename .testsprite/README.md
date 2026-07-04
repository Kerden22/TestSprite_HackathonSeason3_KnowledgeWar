# TestSprite local artifacts — KnowledgeWar

Organized test evidence for hackathon / jury. All tests from **LOOP.md** (iterations 2–6) in **one flat index per verdict** — no per-iteration subfolders.

**Project:** `1839c68e-2f6e-497e-a25f-7c9b798a7c1a`  
**Live URL:** https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com

## Start here

| File | What |
|------|------|
| **`manifest-all.json`** | Complete suite — all iterations, verdicts, plans, run IDs |
| `pass/manifest.json` | 28 PASS (iter 2–6 combined) |
| `blocked/manifest.json` | 8 BLOCKED (all waived) |
| `failure/manifest.json` | 1 FAILED (`ebe0b04d`, fixed) |

## Folder layout

```
.testsprite/
├── manifest-all.json
├── pass/
│   └── manifest.json              ← all PASS tests, all iterations
├── blocked/
│   ├── manifest.json              ← all BLOCKED tests, all iterations
│   └── a4bd6c04-learn-smoke/      ← only downloaded artifact bundle
└── failure/
    └── manifest.json              ← all FAILED tests, all iterations
```

Each test entry has an `iteration` field (2–6) instead of separate subfolders.

## Verdict summary

| Verdict | Count | Notes |
|---------|------:|-------|
| PASS | 28 | incl. `ebe0b04d` re-run |
| BLOCKED | 8 | All waived — app works |
| FAILED | 1 | Fixed |

**Iter 6 CI:** 13 PASS / 1 BLOCKED → functional **14/14**  
**Unique tests:** 36 (25 FE + 11 BE)

## FE plans & BE scripts

- Plans: [`testsprite-plans/`](../testsprite-plans/) (`01`–`25`)
- BE tests: [`testsprite/tests/`](../testsprite/tests/)

## Hackathon form

> Does your repository contain a `.testsprite/failure/` subfolder?

**Yes** — plus `pass/` and `blocked/`. See `manifest-all.json`.

## Download artifacts

```bash
testsprite test artifact get <runId> --out ./.testsprite/blocked/<testId-short-name>
```

Run IDs are in each `manifest.json` and `manifest-all.json`.
