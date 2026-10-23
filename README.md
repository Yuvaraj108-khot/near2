# Chakravyuh Sovereign Settlement Gateway

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

**Category**: Web / Fintech Protocols  
**Difficulty**: Medium  
**Points**: 175  
**Flag Format**: `CHAKRAVYUHA{...}`

> The Vyūha Clearing Engine orchestrates sovereign inter-institution liquidity settlements across concentric rings of validation. Built on the Saptaratha settlement architecture, every settlement instruction submitted to the clearinghouse is cryptographically attested by the sovereign liquidity vault, strictly ordered, and committed to double-entry ledger journals.
>
> Your institution has been allocated an operational settlement channel backed by pooled sovereign liquidity reserves. Clear funds through the concentric rings, monitor reserve adequacy against statutory requirements, and maintain institutional compliance with clearinghouse supervisory oversight.

---

## Architecture & Features

- **Concentric Settlement Rings**: Multi-tier clearance pipeline (`Intake` → `Earmark` → `Disburse` → `Finalize`).
- **Sound Cryptographic Attestation**: Ed25519 digital signatures with canonical JSON serialization.
- **Double-Entry Ledger**: Immutable posted journals and cryptographic clearance vouchers.
- **Interactive Web Terminal**: Full-featured dark-mode UI with live telemetry, visual ring progress, and ledger explorer.
- **Deploy Anywhere**: Runs as a standard FastAPI Python server, a Docker container, or serverless on Vercel.

---

## Quick Start

### Option 1: Run with Python Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application server
python application/main.py
```

The gateway dashboard will be available at **`http://localhost:8000/`**.

### Option 2: Run with Docker Compose

```bash
docker compose up --build
```

Access the application at **`http://localhost:8000/`**.

### Option 3: Deploy to Vercel

This repository is pre-configured for Vercel deployment:
- Entry point: `api/index.py`
- Configuration: `vercel.json`
- Storage: Automatically uses `/tmp/settlement.db` in serverless environments

Push to your GitHub repository and import it directly into Vercel.

---

## REST API Overview

```http
POST /api/channel/open               Initialize an operational clearing channel
GET  /api/channel/status             Query channel balance, stage, and reserve ratio
GET  /api/instructions/manifest      Retrieve pre-authorized sovereign treasury manifest
POST /api/pipeline/intake            Submit signed settlement manifest for Ring I intake
POST /api/pipeline/earmark           Authorize Ring II collateral reservation
POST /api/pipeline/disburse          Execute Ring III double-entry ledger mutation
POST /api/receipts/finalize          Seal Ring IV batch and issue settlement certificate
POST /api/channel/reconcile          Trigger supervisory reserve and capital compliance review
```

---

## Repository Structure

```text
.
├── api/
│   └── index.py             # Vercel serverless function entrypoint
├── application/
│   ├── main.py              # Application startup & routes
│   ├── config.py            # Protocol thresholds & config
│   ├── database.py          # SQLAlchemy models & database engine
│   ├── core/                # Ed25519 crypto & security utilities
│   ├── models/              # Database models (Channel, Staging, Journal, Receipt)
│   ├── services/            # Pipeline, ledger, & supervisory business logic
│   ├── routers/             # REST API endpoints
│   ├── static/              # Interactive dashboard UI (HTML, CSS, JS)
│   └── data/                # Pre-signed sovereign manifest
├── challenge/               # Participant package & challenge definition
├── organizer/               # Organizer files (description.md, flag.txt, walkthrough.md)
├── docker-compose.yml       # Docker Compose service definition
├── Dockerfile               # Docker containerfile
├── vercel.json              # Vercel deployment routing configuration
└── requirements.txt         # Python package dependencies
```
