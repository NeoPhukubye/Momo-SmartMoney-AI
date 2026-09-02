# MoMo SmartMoney AI

> **AI-Powered Financial Coach for MTN MoMo Users in South Africa**
> 
> Scam Shield | Stokvel Intelligence | Multi-Channel Access | Powered by Google Gemini AI
> 
> **MTN Group Fintech Hackathon 2026** | Created by Neo Phukubye

## The Problem

75% of South African mobile money users have encountered scam attempts. Informal savings groups (stokvels) manage R50+ billion annually with zero digital tooling. Feature phone users are locked out of modern fintech.

## The Solution

SmartMoney AI is a financial coach that meets users where they are — on smartphones via a responsive web app, on feature phones via USSD (`*141*8#`), or through voice/IVR. It uses Google Gemini AI to provide personalized, culturally-aware financial guidance in South African English.

## Key Features

| Feature | Description |
|---------|-------------|
| **AI Financial Coach** | Personalized budgeting advice powered by Gemini 2.0 Flash with conversation memory |
| **Scam Shield** | Real-time 5-rule fraud scoring (velocity, reported numbers, scam keywords, unusual amounts, new recipients) |
| **Stokvel Intelligence** | Group savings management with contribution tracking and payout rotation |
| **Multi-Channel** | Web app + USSD + Voice/IVR — reaching 100% of MoMo users |
| **Smart Categorization** | Auto-categorize transactions for spending insights |

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React 18 + Vite 5 + TailwindCSS | Fast, mobile-first PWA |
| Backend | FastAPI (Python 3.11) | Async, high-performance |
| AI Engine | **Google Gemini 2.0 Flash** | Fast inference, conversational, cost-effective |
| Database | PostgreSQL 15 (via Render) | Reliable, auto-managed |
| Payments | MTN MoMo API | Collection + Disbursement |
| USSD | Africa's Talking | Feature phone access |
| Hosting | **Render.com** | One-click deploy, auto-scaling, free tier |

## Deploy to Render (One-Click)

### Prerequisites
1. A [Render.com](https://render.com) account (free)
2. A [Google AI Studio](https://aistudio.google.com/apikey) API key (free)
3. This repo pushed to GitHub

### Steps

1. **Connect your repo to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **New** > **Blueprint**
   - Connect your GitHub repo
   - Render reads `render.yaml` and auto-creates all services

2. **Set secret environment variables** (in Render dashboard):
   - `GEMINI_API_KEY` — your Google AI Studio key
   - `MOMO_COLLECTION_PRIMARY_KEY` — MTN MoMo sandbox key
   - `MOMO_API_USER` — MTN MoMo API user UUID
   - `MOMO_API_KEY` — MTN MoMo API key
   - `AT_API_KEY` — Africa's Talking key (for USSD)

3. **Deploy** — Render auto-builds and deploys:
   - `smartmoney-api.onrender.com` — Backend API
   - `smartmoney-app.onrender.com` — Frontend PWA
   - `smartmoney-db` — PostgreSQL database

### What Render Provides
- Auto-deploy on every `git push`
- Free PostgreSQL database
- Free SSL/TLS certificates
- Health check monitoring
- Zero-downtime deploys

## Local Development

```bash
# 1. Clone and setup
git clone https://github.com/your-username/Momo-SmartMoney-AI.git
cd Momo-SmartMoney-AI
cp .env.example .env
# Edit .env — at minimum set GEMINI_API_KEY

# 2. Backend
cd backend
pip install -r requirements.txt
python seed.py          # Load demo data
uvicorn app.main:app --reload

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

**Demo login:** phone `0712345678`, PIN `1234`

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register with phone + PIN |
| POST | `/api/auth/login` | Login, get JWT |
| GET | `/api/transactions/` | List user transactions |
| GET | `/api/transactions/summary` | 30-day spending breakdown |
| GET | `/api/transactions/flagged` | Scam-flagged transactions |
| POST | `/api/coaching/chat` | Chat with AI coach (Gemini) |
| GET | `/api/coaching/tips` | Daily financial tips |
| POST | `/api/stokvels/` | Create a stokvel group |
| GET | `/api/stokvels/` | List user's stokvels |
| POST | `/api/ussd/callback` | Africa's Talking USSD webhook |
| GET | `/health` | Service health + DB status |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTS                                    │
│  Smartphone (PWA)  │  Feature Phone (USSD)  │  IVR (Voice) │
└────────────┬───────────────┬──────────────────┬─────────────┘
             │               │                  │
┌────────────▼───────────────▼──────────────────▼─────────────┐
│                     FastAPI Backend                           │
│                    (Render.com)                               │
├──────────────┬─────────────────┬────────────────────────────┤
│  AI Coach    │   Scam Shield   │   Stokvel Engine           │
│  (Gemini AI) │   (5 rules)     │   (Group savings)          │
│  + Memory    │   + Community    │   + Rotation tracking      │
│              │     reports      │                            │
├──────────────┴─────────────────┴────────────────────────────┤
│  PostgreSQL (Render)  │  MTN MoMo API  │  Africa's Talking  │
└───────────────────────┴────────────────┴────────────────────┘
```

## Google Gemini AI Integration

SmartMoney uses **Gemini 2.0 Flash** for:
- Personalized financial coaching with user transaction context
- Multi-turn conversation memory (remembers past interactions)
- Culturally-aware responses using South African English
- Smart suggestion generation based on spending patterns
- Graceful fallback to rule-based responses when API is unavailable

**Cost:** Gemini 2.0 Flash free tier provides 15 RPM / 1M TPM — sufficient for demo and early users.

## Hackathon Differentiators

1. **Inclusive by design** — USSD access means 100% of MoMo users can benefit, not just smartphone owners
2. **AI with context** — Gemini sees your actual spending data, not generic advice
3. **Scam protection** — Proactive fraud detection on every outgoing transaction
4. **Community savings** — Digital stokvels bring R50B+ in informal savings into the digital era
5. **Zero infrastructure cost** — Runs entirely on Render.com free tier + Gemini free tier

## License

Built for MTN Group Fintech Hackathon 2026 by Neo Phukubye.
