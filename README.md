# MoMo SmartMoney AI

> **AI-Powered Financial Coach & Cardless Tap-to-Pay for MTN MoMo Users in South Africa**  
> *Scam Shield · Stokvel Intelligence · Cardless Tap-to-Pay (Apple Pay & Google Wallet) · QR Scan-to-Pay · Multi-Channel Access · Powered by Google Gemini AI*  

🌐 **Live demo:** [neophukubye.github.io/Momo-SmartMoney-AI](https://neophukubye.github.io/Momo-SmartMoney-AI/)  
🔌 **API:** [momo-smartmoney-ai.onrender.com/docs](https://momo-smartmoney-ai.onrender.com/docs)

---

## 📌 The Problem
* **Fraud Epidemic:** 75% of South African mobile money users have encountered scam attempts.
* **Informal Finance Blindspots:** Informal savings groups (stokvels) manage R50+ billion annually with zero digital tooling, relying on fragmented chats and memory.
* **POS & Card Barriers:** Physical retail checkout overwhelmingly favors contactless cards and phone wallets (Apple Pay / Google Pay), leaving standard mobile money users stuck with slow QR codes or cash withdrawals.
* **Digital Exclusion:** Millions of feature phone users remain completely locked out of modern fintech apps and automated budgeting tools.

---

## 💡 The Solution
SmartMoney AI transforms MTN MoMo from a basic transaction wallet into a proactive, intelligent financial companion:
* **Cardless Tap & Pay:** Generates virtual tokenized MoMo cards backed directly by wallet balances, ready for push-provisioning into Apple Pay, Google Wallet, and Samsung Wallet for instant NFC POS checkout.
* **In-app Wallet + Scan-to-Pay:** Every user has a SmartMoney wallet. Scan a MoMo / Stokvel QR code (camera or upload) to populate a top-up or withdrawal in one tap; pending transactions are auto-synced against the MoMo sandbox.
* **Real-Time Scam Shield:** Evaluates outgoing transfers and POS authorizations against a 5-rule fraud scoring engine before money leaves the wallet.
* **Stokvel Intelligence:** Manages rotational community group savings with a **mandatory MTN-member rule** and equal member authority.
* **Multi-Channel Delivery:** Web PWA, USSD (`*141*8#`) and Voice / IVR powered by Google Gemini AI.

---

## 🚀 Key Features

* **Cardless Tap & Pay (Apple Pay / Google Wallet):** Virtual card tokenization for contactless in-store POS tapping and secure web checkout directly against MoMo balances.
* **SmartMoney Wallet:** Per-user balance, MoMo Request-to-Pay top-up / withdrawal, Google Wallet enrolment, and a live activity feed that polls the MoMo sandbox until each transaction succeeds or fails.
* **QR Scan-to-Pay:** `jsQR`-powered scanner with camera + image upload fallback. Scans are normalised server-side to a typed payload (`momo_pay`, `momo_request`, `stokvel_invite`, …) so the UI can pre-fill the top-up form.
* **Scam Shield AI:** 5-rule fraud scoring (velocity, reported scam numbers, suspicious keywords, unusual transfer amounts, first-time recipients).
* **Stokvel Intelligence:** Group savings ledger with contribution tracking, payout rotation, and an MTN-member requirement that prevents non-MTN members from creating a Stokvel.
* **AI Financial Coach:** Personalized budgeting advice, spending categorization, and natural-language Q&A powered by Google Gemini 2.0 Flash with conversation memory.
* **Multi-Channel Access:** Web PWA, USSD (`*141*8#`), and voice prompts, all backed by the same FastAPI core.
* **Accessibility-first:** WCAG-friendly colour contrast, dyslexia-friendly font, high-contrast / dark-mode / reduced-motion modes, large touch targets, screen-reader-friendly labels.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite 5, TailwindCSS, jsQR | Mobile-first PWA with QR scanning & digital-wallet hooks |
| **Backend** | FastAPI · Python 3.11 · Uvicorn · Gunicorn | Async, high-concurrency API & orchestrator |
| **AI Engine** | Google Gemini 2.0 Flash | Conversational coaching, spending pattern insights, and memory |
| **Database** | PostgreSQL 15 (Render) | ACID persistence for users, wallets, cards, stokvel ledgers |
| **Virtual Card & NFC** | MoMo Virtual Card API / tokenization | Cardless token generation for Apple Pay & Google Wallet |
| **Payments** | MTN MoMo API (collection) | Request-to-Pay flows for wallet top-up / withdrawal |
| **USSD Gateway** | Africa's Talking | `*141*8#` sessions for feature-phone users |
| **Hosting** | GitHub Pages (frontend) + Render.com (backend) | Free-tier, auto-deploy on push to `main` |

---

## 📐 Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                                CLIENTS                                 │
│  Smartphone (PWA)  │  Digital Wallets (Apple/Google)  │  USSD / IVR   │
└──────────┬────────────────────────┬───────────────────────┬────────────┘
           │                        │                       │
┌──────────▼────────────────────────▼───────────────────────▼────────────┐
│                      FastAPI Backend (Render.com)                      │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────┤
│   AI Coach   │  Scam Shield │  Stokvel     │  SmartMoney  │  Card &     │
│  (Gemini 2.0 │  (5 rules +  │  Engine      │  Wallet      │  Wallet     │
│   Flash +    │   risk warn) │  + MTN rule  │  + Scan QR   │  Provision  │
│   memory)    │              │  + equality  │  + RTP sync  │  (Apple/G)  │
├──────────────┴──────────────┴──────────────┴──────────────┴─────────────┤
│   PostgreSQL (Render)   │   MTN MoMo API   │  Apple / Google Wallet    │
└─────────────────────────┴──────────────────┴───────────────────────────┘
```

---

## 🧱 Project Layout

```text
.
├── backend/                # FastAPI app (Python 3.11, async)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── utils.py            # phone/MTN helpers
│   │   ├── models/             # SQLAlchemy models (incl. Wallet, WalletTransaction)
│   │   ├── schemas/            # Pydantic models
│   │   ├── routers/            # auth, transactions, coaching, stokvel, payments, wallet, cards, ussd, voice
│   │   └── services/           # momo.py, momo_api.py, ...
│   ├── requirements.txt
│   ├── runtime.txt            # python-3.11.9
│   └── Dockerfile
├── frontend/               # React 18 + Vite 5 + TailwindCSS
│   ├── src/
│   │   ├── pages/              # Login, Dashboard, Chat, Stokvel, Transactions, Wallet
│   │   ├── components/         # Layout, QRScanner, GooglePayCheckout, AccessibilityPanel, ...
│   │   ├── services/api.js     # axios client (VITE_API_URL → Render backend)
│   │   ├── context/            # AccessibilityContext
│   │   ├── locales/            # i18next translations (16 African languages)
│   │   └── index.css
│   ├── vite.config.js          # base: '/Momo-SmartMoney-AI/'
│   ├── tailwind.config.js
│   └── package.json
├── render.yaml            # Render blueprint (DB + API only; frontend hosted on GH Pages)
└── README.md
```

---

## ⚙️ Local Development

```bash
# Backend
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in DATABASE_URL, GEMINI_API_KEY, MOMO_*
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev   # http://localhost:5173 (proxies /api to localhost:8000)
```

> Set `VITE_API_URL` in `frontend/.env.local` if you want the dev frontend to hit a non-default API host.

---

## 🚀 Deployment

* **Frontend** → GitHub Pages, auto-deployed by `.github/workflows/deploy.yml` on every push to `main`.
* **Backend** → Render.com via the blueprint in `render.yaml`. The service runs Gunicorn + Uvicorn workers behind `$PORT` inside a Python 3.11.9 Docker image.

Key `render.yaml` env vars:

| Var | Purpose |
| :--- | :--- |
| `DATABASE_URL` | Linked from the internal Render Postgres |
| `SECRET_KEY` | JWT signing (auto-generated) |
| `MOMO_BASE_URL` | `https://proxy.momoapi.mtn.com/collection` |
| `MOMO_TARGET_ENVIRONMENT` / `MOMO_ENVIRONMENT` | `mtnsouthafrica` (production-proxy keys) |
| `MOMO_COLLECTION_PRIMARY_KEY`, `MOMO_DISBURSEMENT_KEY`, `MOMO_API_USER`, `MOMO_API_KEY` | MoMo credentials (set in dashboard) |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Google AI Studio key + `gemini-2.0-flash` |
| `AT_API_KEY`, `AT_USERNAME` | Africa's Talking (USSD) |
| `CORS_ORIGINS` | `https://neophukubye.github.io,http://localhost:5173` |

---

## 🧪 Quick smoke tests

```bash
# Health
curl https://momo-smartmoney-ai.onrender.com/health

# Wallet balance (replace TOKEN with a logged-in JWT)
curl -H "Authorization: Bearer $TOKEN" https://momo-smartmoney-ai.onrender.com/api/wallet

# Scan parser
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"raw":"momo://pay?amount=10&phone=0831234567&ref=abc"}' \
  https://momo-smartmoney-ai.onrender.com/api/wallet/scan
```

---

## 🛡️ Security & Privacy
* PIN + JWT auth on every protected endpoint.
* Scam Shield flags high-risk merchants and velocity before any tap-to-pay authorization.
* No raw card PANs ever leave the backend — only opaque MDES tokens.
* All MoMo calls go through the official MTN collection proxy with Basic Auth + subscription key.

---

## 📄 License

MIT — see `LICENSE`.

---

**MTN Group Fintech Hackathon 2026** | Created by **Neo Phukubye**
