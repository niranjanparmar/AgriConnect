# AgriConnect 🌱🛒📊
> **Integrated Direct Farmer-to-Consumer Marketplace & APMC Mandi Price Intelligence Platform**  
> *Developed for Marwadi University / College — Department of Computer Engineering / IT (IPE Capstone Project)*

![Python](https://img.shields.io/badge/Python-3.11.9-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?logo=bootstrap&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?logo=chartdotjs&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-49%20Passed%20(100%25)-success?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-Academic%20Use-green)

---

## 🌾 Project Overview

**AgriConnect** is an enterprise-grade agricultural web application designed to bridge the economic gap between Indian farmers and end consumers while solving wholesale price asymmetry. Built from scratch with Python, Flask, PostgreSQL/SQLAlchemy, and Bootstrap 5, it integrates two complementary operational modules:

1. **Module A — Direct Farmer-to-Consumer Marketplace:**
   - Role-based accounts for verified agricultural producers and retail consumers.
   - Farmer harvest management with **local image uploads and mobile camera capture**.
   - Persistent shopping cart, server-side stock validation, and atomic cash-on-delivery transactions.
   - Complete order fulfillment lifecycle (Pending &rarr; Confirmed &rarr; Shipped &rarr; Delivered &rarr; Cancelled) with historical price snapshots.

2. **Module B — APMC Mandi Crop Price Intelligence:**
   - Ingestion and synchronization service for Indian agricultural wholesale market data conforming to official **Agmarknet / data.gov.in** schemas.
   - Deterministic SHA-256 fingerprint hashing guaranteeing **zero duplicate imports**.
   - Mathematical bounds validation ($\text{min\_price} \le \text{modal\_price} \le \text{max\_price}$).
   - Multi-mandi comparative spreads and 7-day historical price trends visualized with **Chart.js**.
   - Automated user price alert rule engine.

---

## 🚀 Quickstart Guide (Windows PowerShell)

### 1. Clone & Set Up Virtual Environment
```powershell
cd "c:\Marwadi college\IPE Assignment\IPE Web Application"

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

# Seed realistic produce categories, demo farmers, consumers, and listings
flask cli seed

# Ingest verified Agmarknet APMC mandi daily benchmark rates
flask cli sync-prices --source demo --limit 50
```

### 4. Run Automated Test Suite (49 Tests)
```powershell
pytest -v
```

### 5. Launch the Web Application
```powershell
python run.py
```
Open **http://127.0.0.1:5000** in your browser.

---

## 🔑 Demo Login Credentials

| Role | Email Address | Password | Permissions & Dashboard |
| :--- | :--- | :--- | :--- |
| **Farmer** | `farmer@agriconnect.org` | `FarmerPass123!` | Publish produce, camera uploads, inventory management, fulfill inbound orders |
| **Consumer** | `consumer@agriconnect.org` | `ConsumerPass123!` | Browse produce, shopping cart, cash-on-delivery checkout, order tracking |

*(New farmers and consumers can also register independently via the registration portal).*

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
  • Login / Register     • Browse & Search               • Cart Management        • APMC Daily Rates
  • Role-Based RBAC      • Camera/Local Upload           • Transactional Checkout • Mandi Comparison
  • Session Security     • Produce Inventory             • Status Lifecycle       • Chart.js Trends
         │                        │                               │                        │
         └────────────────────────┼───────────────────────────────┴────────────────────────┘
                                  ▼
                     [ SQLAlchemy 2.0 ORM Engine ]
                                  │
         ┌────────────────────────┴───────────────────────────────┐
         ▼                                                        ▼
[ SQLite (Local Testing) ]                              [ PostgreSQL (Production) ]
• 12 Normalized Models                                  • High-Concurrency Transactions
• Fixed-Precision Numerics                              • Cascade Constraints & Foreign Keys
```

---

## 🔒 Security Architecture Highlights

- **CSRF Token Defense**: Every POST form carries a synchronized CSRF token preventing cross-site request forgery.
- **Password Security**: Passwords hashed using industry-standard Werkzeug `scrypt` / `pbkdf2:sha256` key derivation.
- **Safe File Uploads**: Validated file extensions (`PNG`, `JPG`, `JPEG`, `WEBP`), `secure_filename` path traversal sanitization, and UUID collision defense.
- **HTTP Security Headers**: Automated `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `X-XSS-Protection`.
- **Role Isolation**: Strict `@farmer_required` and `@consumer_required` decorators preventing cross-role privilege escalation.
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
```

---

## 📄 Academic Project Documentation

The complete engineering report with ER Diagrams, Sequence Diagrams, Test Matrices, and Academic Literature Citations is available at [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md).

