#!/bin/bash
# Full demo script for IntelliBlue SOC
set -e

echo "=== IntelliBlue SOC Demo Setup ==="
echo ""

cd "$(dirname "$0")/.."

# Start PostgreSQL (if using docker-compose)
if command -v docker-compose &> /dev/null; then
    echo "Starting PostgreSQL..."
    docker-compose up -d postgres
    sleep 5
fi

# Run migrations
echo "Running database migrations..."
cd backend
alembic upgrade head

# Seed users
echo "Seeding users..."
python ../scripts/seed_users.py

# Seed demo data
echo "Seeding demo data..."
python ../scripts/seed_demo_data.py

# Start backend
echo ""
echo "Starting backend on http://localhost:8000 ..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
cd ../frontend
echo "Installing frontend dependencies..."
npm install --silent

echo "Starting frontend on http://localhost:5173 ..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== IntelliBlue SOC is running ==="
echo "  Frontend: http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Default credentials:"
echo "  admin / admin123  (ADMIN role)"
echo "  analyst1 / analyst123  (L1 role)"
echo "  analyst2 / analyst123  (L2 role)"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
