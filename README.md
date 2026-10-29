# AgriConnect India 🌱🛒📊
> **National Direct Farmer-to-Consumer Agricultural Marketplace & Real-Time APMC Mandi Price Intelligence Platform**

![Python](https://img.shields.io/badge/Python-3.11.9-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?logo=bootstrap&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?logo=chartdotjs&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-53%20Passed%20(100%25)-success?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌾 Platform Overview

**AgriConnect India** is a modern full-stack agricultural platform designed to bridge the economic divide between Indian growers and consumers while solving wholesale price asymmetry. Built with Python 3.11, Flask 3.0, PostgreSQL/SQLAlchemy, and Bootstrap 5, it unites two core commercial modules:

1. **Direct Farmer-to-Consumer Marketplace:**
   - Role-based accounts for verified agricultural producers and retail consumers.
   - Farm harvest listing management with **local image uploads and direct mobile camera capture**.
   - Persistent shopping cart, server-side stock validation, and atomic cash-on-delivery transactions.
   - Order fulfillment lifecycle (Confirmed &rarr; Dispatched &rarr; Delivered &rarr; Cancelled) with historical price snapshots.

2. **APMC Mandi Price Intelligence & AI Forecasting:**
   - Real-time synchronization service for Indian wholesale mandi data conforming to official **Agmarknet / data.gov.in** schemas.
   - Deterministic SHA-256 fingerprint hashing guaranteeing **zero duplicate imports**.
   - Multi-mandi comparative rate spreads and 7-day historical price trends visualized with **Chart.js**.
   - **Pan-India Price Prediction Engine**: Computes time-series trend slopes, 85% volatility confidence bands, and state-by-state price forecasting.
   - Automated rate alert trigger engine notifying farmers when commodities reach target rates.

---

## 🚀 Quickstart Guide (Windows PowerShell)

### 1. Setup Virtual Environment
```powershell
# Create virtual environment if not already present
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```powershell
# Run database schema migrations
flask db upgrade

# Seed initial categories, demo farmers, consumers, and listings
flask cli seed

# Ingest real live Agmarknet APMC mandi daily rates (or demo benchmark)
flask cli sync-prices --source auto --limit 50
```

### 4. Run Automated Test Suite (53 Tests)
```powershell
pytest -v
```

### 5. Launch the Web Application
```powershell
python run.py
```
Open **http://127.0.0.1:5000** in your browser.

---

## 🏛️ System Architecture

```
                                  [ Web Client (Browser / Mobile) ]
                                                  │
                                                  ▼
                                      [ Flask 3.0 App Factory ]
                                                  │
         ┌────────────────────────┬───────────────┴───────────────┬────────────────────────┐
         ▼                        ▼                               ▼                        ▼
  [ Auth Blueprint ]     [ Market Blueprint ]            [ Orders Blueprint ]     [ Prices Blueprint ]
  • Secure Sessions      • Browse & Search               • Cart Management        • Live APMC Mandi Sync
  • Role-Based RBAC      • Camera & File Upload          • Transactional Checkout • Inter-Mandi Spread
  • Password Hashing     • Produce Inventory             • Status Lifecycle       • AI 7-Day Forecasting
         │                        │                               │                        │
         └────────────────────────┼───────────────────────────────┴────────────────────────┘
                                  ▼
                     [ SQLAlchemy 2.0 ORM Engine ]
                                  │
         ┌────────────────────────┴───────────────────────────────┐
         ▼                                                        ▼
[ SQLite (Local Development) ]                          [ PostgreSQL (Production) ]
• 12 Normalized Models                                  • High-Concurrency Transactions
• Fixed-Precision Numerics                              • Foreign Key Cascades & Constraints
```

---

## 🔒 Security Architecture Highlights

- **CSRF Token Protection**: Every POST form carries a synchronized CSRF token preventing cross-site request forgery.
- **Password Security**: Passwords hashed using industry-standard Werkzeug `scrypt` key derivation.
- **Safe File Uploads**: Validated file extensions (`PNG`, `JPG`, `JPEG`, `WEBP`), `secure_filename` path traversal sanitization, and UUID collision defense.
- **HTTP Security Headers**: Automated `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `X-XSS-Protection`.
- **Role Isolation**: Strict `@farmer_required` and `@consumer_required` decorators preventing unauthorized access.
- **Financial Arithmetic**: Decimal fixed-precision `Numeric(10, 2)` throughout; zero floating-point roundoff errors.

---

## ☁️ Cloud Deployment (Render / Railway / Heroku)

A pre-configured `Procfile` and `render.yaml` are included for instant deployment:

```
web: gunicorn run:app
```

Environment variables required in production:
```ini
FLASK_ENV=production
SECRET_KEY=<generate-strong-random-hex-string>
DATABASE_URL=postgresql://user:password@host:5432/agriconnect
AGRI_PRICE_API_KEY=your_datagov_in_api_key
```

---

## 📄 License

This software is released under the **MIT License**.
