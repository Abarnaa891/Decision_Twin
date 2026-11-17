# DecisionTwin AI

An extensible, multi-industry decision intelligence platform combining Data Science, Machine Learning and AI.

## Phase 1 starter scope
- Upload a CSV dataset through FastAPI.
- Profile columns, missing values, numeric summaries and correlations.
- Store dataset metadata in PostgreSQL (Docker) or SQLite (local fallback).
- Run a deterministic what-if simulation against a demo retail dataset.
- React frontend starter with dataset upload and scenario form.

> The demo simulator is intentionally transparent and illustrative. It uses a simple price-elasticity assumption, not a trained causal model. Do not interpret its output as a guaranteed real-world outcome.

## Architecture
- `frontend/`: React + Vite.
- `backend/`: FastAPI REST API.
- `backend/app/`: API, database models, schemas and services.
- `data/`: demo CSV.
- `docs/`: database schema and architecture notes.

## Requirements
- Python 3.10+
- Node.js 20+
- Git
- Docker Desktop (recommended for PostgreSQL; optional for local SQLite)

## Run locally

### 1. Clone and configure
```bash
git clone <YOUR_GITHUB_REPO_URL>
cd DecisionTwin-AI
```

### 2. Start database (optional but recommended)
```bash
docker compose up -d db
```
The API uses PostgreSQL when `DATABASE_URL` is set. Without it, it uses local SQLite at `./decisiontwin.db`.

### 3. Start backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

### 4. Start frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
Open the Vite URL shown in the terminal (usually http://localhost:5173).

## API examples

Health:
```bash
curl http://127.0.0.1:8000/health
```

Profile demo data:
```bash
curl http://127.0.0.1:8000/api/v1/datasets/demo/profile
```

Run a demo what-if simulation:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"demo","price_change_pct":10,"marketing_change_pct":5,"horizon_days":30}'
```

Upload CSV:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/datasets/upload \
  -F "file=@../data/demo_retail_sales.csv" \
  -F "industry=retail"
```

## GitHub setup
```bash
git init
git add .
git commit -m "Initial DecisionTwin AI Phase 1 scaffold"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/DecisionTwin-AI.git
git push -u origin main
```

Never commit `.env`, credentials, real customer data or large private datasets. Use `.env.example` as a template.

## Cloud deployment outline
1. Provision a managed PostgreSQL database.
2. Deploy `backend/` as a Python web service; set `DATABASE_URL` and `CORS_ORIGINS`.
3. Deploy `frontend/` as a static site; set `VITE_API_BASE_URL` to the backend URL.
4. Enable HTTPS and configure production CORS to only allow your frontend domain.
5. Use object storage for uploaded datasets in a later phase; do not rely on ephemeral server disk.

## Next phases
- Phase 2: train and evaluate forecasting models using time-based splits.
- Phase 3: general scenario engine with industry-specific adapters.
- Phase 4: explainability and optimization.
- Phase 5: LLM assistant with validated structured tool calls.
- Phase 6: authentication, audit trail, tests, monitoring and deployment hardening.
