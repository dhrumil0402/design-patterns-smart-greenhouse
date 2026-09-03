# Smart Greenhouse

A smart-greenhouse monitoring and control platform, built incrementally
across course phases. **Phase 1** establishes a runnable three-tier
skeleton: FastAPI backend, PostgreSQL with Alembic migrations, and a
React + TypeScript frontend shell. It intentionally implements no design
pattern and no business tables yet.

## Prerequisites

| Tool | Minimum version | Verify |
|------|------------------|--------|
| Python | 3.11+ | `python --version` |
| Node.js | 20 LTS | `node --version` |
| Docker Desktop | current | `docker --version` |
| Git | any | `git --version` |

## First-time setup

1. Clone and configure environment
```powershell
   git clone https://github.com/dhrumil0402/design-patterns-smart-greenhouse.git
   cd design-patterns-smart-greenhouse
   Copy-Item .env.example .env
   Copy-Item frontend\.env.example frontend\.env
```
2. Start PostgreSQL
```powershell
   docker compose up -d
   docker compose ps
```
3. Install and prepare the backend
```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -e ".[dev]"
   alembic upgrade head
   cd ..
```
4. Install the frontend
```powershell
   cd frontend
   npm install
   cd ..
```

## Daily start

Run each in its own terminal:
```powershell
# 1. Database
docker compose up -d

# 2. Backend (from backend/, with venv active)
uvicorn main:app --reload --app-dir src --host 0.0.0.0 --port 8000

# 3. Frontend (from frontend/)
npm run dev
```

## URLs

| What | URL |
|------|-----|
| API root | http://localhost:8000/ |
| Health check | http://localhost:8000/health |
| Scalar API reference | http://localhost:8000/scalar |
| OpenAPI schema | http://localhost:8000/openapi.json |
| Frontend dashboard | http://localhost:5173/dashboard |

> Built-in Swagger (`/docs`) is disabled — this course uses Scalar instead.

See [`docs/phases/README.md`](docs/phases/README.md) for the phase order.
