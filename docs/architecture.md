# Architecture Overview

## High-Level Design

IntelliBlue is a client-server application:
- **Frontend**: React SPA (Vite) served at port 5173
- **Backend**: FastAPI async REST API at port 8000
- **Database**: PostgreSQL 16 with JSONB columns

## Component Map

```
backend/app/
├── main.py                 # FastAPI app, CORS, router registration
├── config.py               # Pydantic Settings (env vars)
├── database.py             # Async SQLAlchemy engine + session factory
├── models/                 # ORM models (SQLAlchemy)
├── schemas/                # Pydantic v2 request/response schemas
├── api/                    # Route handlers (FastAPI routers)
├── middleware/
│   ├── rbac.py             # Role-based access control (Depends)
│   └── audit.py            # Audit logging helper
├── ingestion/              # Log parsing → NormalizedEvent
│   ├── pipeline.py         # ingest_event() + ingest_batch()
│   ├── siem_parser.py      # SIEM JSON / NDJSON
│   ├── web_parser.py       # Combined Log Format
│   ├── ids_parser.py       # Suricata + Snort
│   ├── normalizer.py       # NormalizedEvent dataclass
│   └── file_handler.py     # SHA-256 + file storage
├── correlation/            # Incident creation engine
│   ├── engine.py           # Orchestrates all rules
│   └── rules/
│       ├── brute_force.py
│       ├── web_scanning.py
│       └── ids_confirmed.py
├── llm/                    # Local LLM interface
│   ├── runtime.py          # llama-cpp-python wrapper
│   ├── summarizer.py       # Incident summarization
│   └── chat_engine.py      # Chat with RAG retrieval
├── retrieval/              # Keyword search + context builder
├── reporting/              # PDF generation (ReportLab)
└── streaming/              # Future streaming placeholders
```

## Data Flow

```
Upload files → file_handler (SHA-256, store)
            → parser (SIEM/Web/IDS) → NormalizedEvent
            → ingest_batch → Event rows (PostgreSQL)
            → correlate_dataset → Incident rows
            → summarize (optional) → IncidentAISummary rows
            → UI displays incidents + chatbot
```

## Security Model

- JWT tokens (HS256) with 8-hour expiry
- bcrypt password hashing (cost factor 12)
- RBAC enforced via FastAPI Depends chain
- All privileged actions recorded in audit_log
- Prompt injection defense: logs treated as untrusted text
