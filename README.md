# MoMo SmartMoney AI

> **AI-Powered Financial Coach & Cardless Tap-to-Pay for MTN MoMo Users in South Africa**
> *Scam Shield | Stokvel Intelligence | Cardless Tap-to-Pay (Apple Pay & Google Wallet) | Multi-Channel Access | Powered by Google Gemini AI*

**Live demo:** https://neophukubye.github.io/Momo-SmartMoney-AI/
**API:** https://momo-smartmoney-ai.onrender.com — [health check](https://momo-smartmoney-ai.onrender.com/health)

> The API runs on a free Render instance and sleeps when idle. The first request after a quiet period takes up to 50 seconds to wake it.

---

## 📌 The Problem

* **Fraud Epidemic:** 75% of South African mobile money users have encountered scam attempts.
* **Informal Finance Blindspots:** Informal savings groups (stokvels) manage R50+ billion annually with zero digital tooling, relying on fragmented chats and memory.
* **POS & Card Barriers:** Physical retail checkout overwhelmingly favors contactless cards and phone wallets (Apple Pay/Google Pay), leaving standard mobile money users stuck with slow QR codes or cash withdrawals.
* **Digital Exclusion:** Millions of feature phone users remain completely locked out of modern fintech apps and automated budgeting tools.

---

## 💡 The Solution

SmartMoney AI transforms MTN MoMo from a basic transaction wallet into a proactive, intelligent financial companion:

* **Cardless Tap & Pay:** Generates virtual tokenized MoMo cards backed directly by wallet balances, ready for push-provisioning into Apple Pay, Google Wallet, and Samsung Wallet for instant NFC POS checkout.
* **Real-Time Scam Shield:** Evaluates outgoing transfers and POS authorizations against a 5-rule fraud scoring engine before money leaves the wallet.
* **Stokvel Intelligence:** Manages rotational community group savings, contribution tracking, and automated reminders.
* **Multi-Channel Delivery:** Fully functional across Web PWA (smartphones), USSD (`*141*8#` on feature phones), and Voice/IVR powered by Google Gemini AI.

---

## 🚀 Key Features

* **Cardless Tap & Pay (Apple Pay / Google Wallet):** Instant virtual card tokenization for contactless in-store POS tapping and secure web checkout directly against MoMo balances.
* **Scam Shield AI:** Real-time 5-rule fraud scoring (velocity, reported scam numbers, suspicious keywords, unusual transfer amounts, and first-time recipients).
* **Stokvel Intelligence:** Group savings ledger with member contribution tracking, shortfall forecasting, and automated payout rotation scheduling.
* **AI Financial Coach:** Personalized budgeting advice, spending categorization, and natural language Q&A powered by Google Gemini 2.0 Flash with conversation memory.
* **Multi-Channel Access:** Consistent financial engine accessible via responsive Web PWA, USSD menu (`*141*8#`), or voice prompts.
* **16 African languages:** English, Afrikaans, Zulu, Xhosa, Sotho, Tswana, Tsonga, Venda, Northern Sotho, Swahili, Amharic, Hausa, Igbo, Yoruba, French, Portuguese.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite 5, TailwindCSS | Fast, mobile-first responsive PWA with Web NFC/Wallet hooks |
| **Backend** | FastAPI (Python 3.11) | Async, high-concurrency API and orchestrator |
| **AI Engine** | Google Gemini 2.0 Flash | Conversational coaching, spending pattern insights, and memory |
| **Database** | PostgreSQL 15 (Render) | ACID-compliant persistence for wallets, cards, and stokvel ledgers |
| **Virtual Card & NFC** | MoMo Virtual Card API / Tokenization | Cardless token generation for Apple Pay & Google Wallet |
| **Payments** | MTN MoMo API | Sandbox collections and disbursement rails |
| **USSD Gateway** | Africa's Talking | USSD session handling (`*141*8#`) for feature phone users |
| **Hosting** | Render.com (API) + GitHub Pages (PWA) | Automated builds and zero-downtime deployment |

---

## 📐 Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                                CLIENTS                                 │
│   Smartphone (PWA)   │  Digital Wallets (Apple/Google)  │   USSD / IVR │
└─────────────┬──────────────────────────┬───────────────────────┬───────┘
              │                          │                       │
┌─────────────▼──────────────────────────▼───────────────────────▼───────┐
│                     FastAPI Backend (Render.com)                       │
├──────────────────┬──────────────────┬──────────────────┬───────────────┤
│    AI Coach      │   Scam Shield    │  Stokvel Engine  │ Virtual Card  │
│ (Gemini 2.0 Flash│    (5 rules)     │ (Group savings)  │  Tap-to-Pay   │
│    + Memory)     │  + Risk warning  │ + Payout tracker │ Tokenization  │
├──────────────────┴──────────────────┴──────────────────┴───────────────┤
│   PostgreSQL (Render)   │   MTN MoMo API   │  Apple / Google Wallet    │
└─────────────────────────┴──────────────────┴───────────────────────────┘
```

---

## ⚡ Quick Start

### Prerequisites

* Python 3.11
* Node.js 20+
* A Google Gemini API key — free from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 1. Clone and configure

```bash
git clone https://github.com/NeoPhukubye/Momo-SmartMoney-AI.git
cd Momo-SmartMoney-AI
cp .env.example .env
```

Open `.env` and set at minimum `GEMINI_API_KEY`. Everything else has working defaults —
the app falls back to a local SQLite database and rule-based coaching without external keys.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is now on http://localhost:8000. Interactive docs at http://localhost:8000/docs
(enabled whenever `APP_ENV` is not `production`).

Optionally load demo accounts and transactions:

```bash
python seed.py
```

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` to the local backend, so no
extra configuration is needed.

### Docker alternative

```bash
docker compose up --build
```

---

## 🔑 Environment Variables

See `.env.example` for the full list. The ones that matter:

| Variable | Required | Notes |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | For AI coaching | Without it, the coach falls back to rule-based responses |
| `DATABASE_URL` | Production | Defaults to local SQLite; set to a Postgres URL in production |
| `SECRET_KEY` | Production | JWT signing key — must be a strong random value |
| `CORS_ORIGINS` | Production | Comma-separated origins, no paths or trailing slashes |
| `MOMO_API_USER`, `MOMO_API_KEY`, `MOMO_COLLECTION_PRIMARY_KEY` | For live payments | MoMo calls are stubbed without these |
| `AT_API_KEY`, `AT_USERNAME` | For USSD | Africa's Talking credentials |
| `VITE_API_URL` | Frontend build | Absolute API URL, baked in at build time |

---

## 🚢 Deployment

**Backend (Render)** — the service builds from `backend/Dockerfile`. Set every variable
from the table above in the dashboard under *Environment*; `render.yaml` is not applied to
manually-created services. `DATABASE_URL` should be the **Internal** database URL, and the
database must be in the same region as the web service.

> Render's free PostgreSQL tier is deleted 30 days after creation. When that happens the API
> returns 502 with `No address associated with hostname` in the logs — create a new database
> and update `DATABASE_URL`.

**Frontend (GitHub Pages)** — `.github/workflows/deploy.yml` builds and publishes on every
push touching `frontend/`. `VITE_API_URL` must be set at build time so the bundle calls the
Render API by absolute URL; GitHub Pages is static hosting and cannot serve `/api/*` itself.

---

## 📡 API Overview

| Endpoint | Purpose |
| :--- | :--- |
| `GET /health` | Service, database and AI status |
| `POST /api/auth/register`, `POST /api/auth/login` | JWT authentication |
| `GET /api/transactions/summary` | Spending summary and categorisation |
| `GET /api/transactions/flagged` | Scam Shield risk assessments |
| `POST /api/coaching/*` | Gemini-backed financial coaching |
| `GET/POST /api/stokvels/*` | Group savings management |
| `POST /api/ussd` | Africa's Talking USSD webhook |
| `POST /api/voice` | Voice/IVR webhook |
| `POST /api/cards/*` | Virtual card issuance and wallet provisioning |

Full interactive documentation at `/docs` in non-production environments.

---

## 📁 Project Structure

```text
backend/
  app/
    routers/     auth, transactions, coaching, stokvel, ussd, voice, cards, payments
    services/    ai_coach, scam_shield, categorizer, momo_api
    models/      SQLAlchemy models
    schemas/     Pydantic schemas
  seed.py        demo data
frontend/
  src/
    pages/       Dashboard, Chat, Stokvel, Transactions, Login
    components/  Layout, VirtualCard, wallet and accessibility components
    locales/     16 language translation files
```

---

**MTN Group Fintech Hackathon 2026** | Created by **Neo Phukubye**
