# KnowledgeWar — TestSprite Hackathon Season 3

Oyunlaştırılmış eğitim ve turnuva platformu. Kullanıcılar kayıt olur, turnuvalara katılır, Gemini AI ile üretilen soruları yanıtlar ve liderlik tablosunda yarışır.

> Bu proje daha önce geliştirilmiş bir tabana sahiptir; bu hackathonda TestSprite CLI ve Cursor ile yeni özellikler eklenerek döngüye sokulmuştur.

## Live Demo

https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com

## GitHub

https://github.com/Kerden22/TestSprite_HackathonSeason3_KnowledgeWar

## Tech Stack

- **Backend:** Python, Flask, SQLite, JWT
- **Frontend:** HTML, JavaScript, Tailwind CSS
- **AI:** Google Gemini (turnuva soru üretimi)
- **Deploy:** Render (free tier)
- **Maker:** Cursor · **Checker:** TestSprite CLI

## Test Coverage (TestSprite E2E)

- Kayıt / giriş akışı (`/login`)
- Turnuva listesi ve katılım (`/tournament`)
- Soru cevaplama / battle (`/battle`)
- Profil sayfası (`/profile`)

## Deploy on Render

After pushing to `master`, Render auto-redeploys. If needed: Dashboard → **Manual Deploy** → Deploy latest commit.

**Required Environment Variables** (Render → Environment):

| Key | Required |
|-----|----------|
| `GEMINI_API_KEY` | Yes |
| `SECRET_KEY` | Recommended |

Start Command: `gunicorn app:app`

## Local Setup

```bash
cd c:\Users\RYZEN\Desktop\tests
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # GEMINI_API_KEY doldur
python app.py
```

Tarayıcı: http://127.0.0.1:5000

## Environment Variables

| Key | Required | Description |
|-----|----------|-------------|
| `GEMINI_API_KEY` | Yes | Turnuva/test soru üretimi |
| `SECRET_KEY` | Recommended | JWT imzalama |
| `GOOGLE_SEARCH_API_KEY` | No | BTK kurs arama (yoksa demo veri) |
| `GOOGLE_CSE_ID` | No | Google Custom Search ID |

Render dashboard → Environment sekmesinden ayarlanır. `.env` dosyası Git'e pushlanmaz.

## Loop

Yaz → Deploy → TestSprite CLI (canlı URL) → Hata → Cursor düzeltir → `LOOP.md` güncellenir.

Detaylı iterasyon logları: [LOOP.md](LOOP.md)
