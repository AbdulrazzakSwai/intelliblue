# 🛡️ IntelliBlue SOC Assistant

A production-shaped **offline** Security Operations Center (SOC) assistant built as a university capstone project. IntelliBlue runs entirely on your laptop — no cloud, no external APIs, no telemetry.

## What Is IntelliBlue?

IntelliBlue ingests security logs (SIEM exports, web server logs, IDS alerts), normalizes and correlates them into security incidents, summarizes incidents using a local LLM, and provides a grounded chatbot Q&A interface inside a SOC dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IntelliBlue SOC                          │
│                                                             │
│  Frontend (React + Vite)                                    │
│  ┌──────────┬───────────┬──────────┬────────────────────┐  │
│  │Dashboard │ Incidents │ Datasets │ Chat | Admin        │  │
│  └──────────┴───────────┴──────────┴────────────────────┘  │
│                    ↕ REST API                               │
│  Backend (FastAPI + SQLAlchemy)                             │
│  ┌────────────┬──────────────┬──────────────────────────┐  │
│  │ Auth/RBAC  │ Ingestion    │  Correlation Engine       │  │
│  │ (JWT)      │ ┌─SIEM JSON  │  ┌─Brute Force Rule      │  │
│  │            │ ├─Web Log    │  ├─Web Scanning Rule      │  │
│  │            │ ├─Suricata   │  └─IDS Confirmed Rule     │  │
│  │            │ └─Snort      │                           │  │
│  ├────────────┴──────────────┴──────────────────────────┤  │
│  │ Local LLM (llama-cpp-python, CPU-first)              │  │
│  │  ├─ Incident Summarizer                              │  │
│  │  └─ Chat Q&A with RAG-like keyword retrieval         │  │
│  ├───────────────────────────────────────────────────── │  │
│  │ PostgreSQL (events, incidents, users, audit log)     │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Log Ingestion**: SIEM JSON (NDJSON/array), Apache/Nginx Combined Log Format, Suricata EVE JSON, Snort JSON
- **Incident Correlation**: 3 explainable rules (brute force, web scanning, IDS-confirmed)
- **Local LLM**: Incident summarization + chatbot Q&A via llama-cpp-python (CPU-first, graceful degradation)
- **RBAC**: L1 (Triage), L2 (Investigation), Admin roles
- **Audit Logging**: All sensitive actions logged
- **PDF Reports**: ReportLab-generated incident reports
- **Streaming-Ready**: Placeholder interfaces for folder-watcher and log-tail agents

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 16** (or Docker)
- **Optional**: GGUF model file for LLM features

## Quick Start (with Docker)

```bash
# 1. Clone and setup
git clone <repo-url>
cd intelliblue
cp .env.example .env

# 2. Start PostgreSQL
docker-compose up -d postgres

# 3. Install dependencies
make setup

# 4. Run migrations + seed data
make db-migrate
make seed

# 5. Start the app
# Terminal 1:
make backend

# Terminal 2:
make frontend

# Open http://localhost:5173
```

## Full Setup (without Docker)

### Backend

```bash
# 1. Install Python dependencies
cd backend
pip install -r requirements.txt

# 2. Configure environment
cp ../.env.example ../.env
# Edit .env with your PostgreSQL credentials

# 3. Create database
createdb intelliblue  # or use psql

# 4. Run migrations
alembic upgrade head

# 5. Seed default users
python ../scripts/seed_users.py

# 6. Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

## Default Credentials

| Username  | Password    | Role  | Permissions |
|-----------|-------------|-------|-------------|
| admin     | admin123    | ADMIN | Full access |
| analyst1  | analyst123  | L1    | View, acknowledge, triage notes, chat |
| analyst2  | analyst123  | L2    | L1 + classify, close, investigation notes |

**⚠️ Change default passwords before any real use!**

## Demo Setup

```bash
# Seed sample data (brute force + web scan + IDS alerts with overlapping IPs)
make seed

# Or run the full demo script
make demo
```

This uploads `sample_data/` files and runs the correlation engine, creating incidents.

## Configuring the LLM (Optional)

```bash
# Download a GGUF model (requires internet - do this before going offline)
bash scripts/download_model.sh

# Place model in ./models/ directory
# Update .env:
LLM_MODEL_PATH=./models/your-model.gguf
LLM_N_GPU_LAYERS=0      # 0 = CPU only
LLM_N_CTX=4096          # Context window
```

Without a model, the system works fully — AI summaries show "LLM not configured".

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/login | Login, get JWT token |
| GET | /datasets/ | List datasets |
| POST | /datasets/ | Upload dataset files |
| GET | /incidents/ | List incidents (with filters) |
| POST | /incidents/{id}/acknowledge | Acknowledge incident (L1+) |
| POST | /incidents/{id}/close | Close incident (L2+) |
| PATCH | /incidents/{id} | Update severity/status (L2+) |
| POST | /incidents/{id}/summarize | Trigger AI summary |
| GET | /reports/incidents/{id}/pdf | Download PDF report (L2+) |
| POST | /chat/sessions | Create chat session |
| POST | /chat/sessions/{id}/messages | Send message, get AI response |
| GET | /admin/audit-log | View audit log (Admin) |
| GET | /users/ | List users (Admin) |
| POST | /users/ | Create user (Admin) |

Full API docs: http://localhost:8000/docs

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

Tests cover: Auth (JWT), RBAC (role enforcement), Ingestion (all parsers), Correlation (brute force rule), Chat (session + message flow).

## RBAC Permissions

| Action | L1 | L2 | Admin |
|--------|----|----|-------|
| View incidents/datasets | ✓ | ✓ | ✓ |
| Acknowledge incidents | ✓ | ✓ | ✓ |
| Add triage notes | ✓ | ✓ | ✓ |
| Chat Q&A | ✓ | ✓ | ✓ |
| Close incidents | ✗ | ✓ | ✓ |
| Edit severity/status | ✗ | ✓ | ✓ |
| Add investigation notes | ✗ | ✓ | ✓ |
| Export PDF reports | ✗ | ✓ | ✓ |
| Upload/delete datasets | ✗ | ✗ | ✓ |
| Manage users | ✗ | ✗ | ✓ |
| View audit log | ✗ | ✗ | ✓ |

## Technology Stack

**Backend**: FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16, Alembic, python-jose (JWT), passlib (bcrypt), ReportLab, llama-cpp-python

**Frontend**: React 18, Vite 5, React Router 6, Axios

## Offline Design

All LLM inference uses llama-cpp-python with local GGUF models. No external API calls. The system gracefully degrades if no model is configured.

## Streaming-Ready Architecture

The core `ingest_event()` function in `backend/app/ingestion/pipeline.py` is the atomic pipeline unit. Placeholder interfaces for `FolderWatcher` and `TailAgent` are in `backend/app/streaming/`.

---

*IntelliBlue SOC — Capstone 2 Project, BSc Cybersecurity*
