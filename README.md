# MoMo SmartMoney AI

> **AI-Powered Financial Coach & Cardless Tap-to-Pay for MTN MoMo Users in South Africa**  
> *Scam Shield | Stokvel Intelligence | Cardless Tap-to-Pay (Apple Pay & Google Wallet) | Multi-Channel Access | Powered by Google Gemini AI*  
> 

---

## 📌 The Problem
* **Fraud Epidemic:** 75% of South African mobile money users have encountered scam attempts.
* **Informal Finance Blindspots:** Informal savings groups (stokvels) manage R50+ billion annually with zero digital tooling, relying on fragmented chats and memory[cite: 1].
* **POS & Card Barriers:** Physical retail checkout overwhelmingly favors contactless cards and phone wallets (Apple Pay/Google Pay), leaving standard mobile money users stuck with slow QR codes or cash withdrawals.
* **Digital Exclusion:** Millions of feature phone users remain completely locked out of modern fintech apps and automated budgeting tools[cite: 1].

---

## 💡 The Solution
SmartMoney AI transforms MTN MoMo from a basic transaction wallet into a proactive, intelligent financial companion:
* **Cardless Tap & Pay:** Generates virtual tokenized MoMo cards backed directly by wallet balances, ready for push-provisioning into Apple Pay, Google Wallet, and Samsung Wallet for instant NFC POS checkout.
* **Real-Time Scam Shield:** Evaluates outgoing transfers and POS authorizations against a 5-rule fraud scoring engine before money leaves the wallet[cite: 1].
* **Stokvel Intelligence:** Manages rotational community group savings, contribution tracking, and automated reminders[cite: 1].
* **Multi-Channel Delivery:** Fully functional across Web PWA (smartphones), USSD (`*141*8#` on feature phones), and Voice/IVR powered by Google Gemini AI[cite: 1].

---

## 🚀 Key Features

* **Cardless Tap & Pay (Apple Pay / Google Wallet):** Instant virtual card tokenization for contactless in-store POS tapping and secure web checkout directly against MoMo balances.
* **Scam Shield AI:** Real-time 5-rule fraud scoring (velocity, reported scam numbers, suspicious keywords, unusual transfer amounts, and first-time recipients)[cite: 1].
* **Stokvel Intelligence:** Group savings ledger with member contribution tracking, shortfall forecasting, and automated payout rotation scheduling[cite: 1].
* **AI Financial Coach:** Personalized budgeting advice, spending categorization, and natural language Q&A powered by Google Gemini 2.0 Flash with conversation memory[cite: 1].
* **Multi-Channel Access:** Consistent financial engine accessible via responsive Web PWA, USSD menu (`*141*8#`), or voice prompts[cite: 1].

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
| **Hosting** | Render.com | Automated builds, free PostgreSQL, zero-downtime deployment |

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

**MTN Group Fintech Hackathon 2026** | Created by **Neo Phukubye**