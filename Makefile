.PHONY: setup db-migrate seed backend frontend demo test clean

# Full setup
setup:
cd backend && pip install -r requirements.txt
cd frontend && npm install
cp -n .env.example .env || true
mkdir -p uploads models

# Run database migrations
db-migrate:
cd backend && alembic upgrade head

# Seed default users and demo data
seed:
cd backend && python ../scripts/seed_users.py
cd backend && python ../scripts/seed_demo_data.py

# Start backend only
backend:
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend only
frontend:
cd frontend && npm run dev

# Run full demo (uses docker-compose for postgres)
demo:
bash scripts/run_demo.sh

# Run backend tests
test:
cd backend && python -m pytest tests/ -v

# Download LLM model (before going offline)
download-model:
bash scripts/download_model.sh

# Start postgres via docker-compose
postgres:
docker-compose up -d postgres

# Stop all docker services
stop:
docker-compose down

# Clean build artifacts
clean:
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
cd frontend && rm -rf dist node_modules/.cache 2>/dev/null || true
