import os, uuid
from pathlib import Path
from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
from .database import Base, engine, get_db
from .models import Dataset, Simulation
from .schemas import SimulationRequest
from .services import load_demo, profile_dataframe, run_retail_demo

Base.metadata.create_all(bind=engine)

# Register the bundled demo dataset so simulation records satisfy the FK.
from .database import SessionLocal
with SessionLocal() as seed_db:
    if seed_db.get(Dataset, "demo") is None:
        seed_db.add(Dataset(id="demo", name="Demo Retail Sales", industry="retail",
                            filename="demo_retail_sales.csv", row_count=180, column_count=5))
        seed_db.commit()

app = FastAPI(title="DecisionTwin AI API", version="0.1.0",
              description="Phase 1 data foundation and transparent demo simulation API")

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in origins],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 15 * 1024 * 1024

@app.get("/health")
def health():
    return {"status": "ok", "service": "DecisionTwin AI"}

@app.get("/api/v1/datasets/demo/profile")
def demo_profile():
    return {"dataset_id": "demo", "industry": "retail",
            "profile": profile_dataframe(load_demo())}

@app.post("/api/v1/datasets/upload")
async def upload_dataset(file: UploadFile = File(...), industry: str = Form("general"),
                         db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported in Phase 1.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File exceeds the 15 MB Phase 1 limit.")
    try:
        from io import BytesIO
        df = pd.read_csv(BytesIO(content))
    except Exception as exc:
        raise HTTPException(400, f"Could not parse CSV: {exc}")
    if df.empty or len(df.columns) == 0:
        raise HTTPException(400, "CSV must contain at least one row and one column.")
    dataset_id = str(uuid.uuid4())
    safe_name = f"{dataset_id}.csv"
    (UPLOAD_DIR / safe_name).write_bytes(content)
    record = Dataset(id=dataset_id, name=Path(file.filename).stem[:255],
                     industry=industry[:50], filename=safe_name,
                     row_count=int(df.shape[0]), column_count=int(df.shape[1]))
    db.add(record)
    db.commit()
    return {"dataset_id": dataset_id, "filename": file.filename,
            "industry": industry, "profile": profile_dataframe(df)}

@app.post("/api/v1/simulations")
def create_simulation(payload: SimulationRequest, db: Session = Depends(get_db)):
    if payload.industry != "retail" or payload.dataset_id != "demo":
        raise HTTPException(400, "Phase 1 simulator currently supports the bundled retail demo only.")
    result = run_retail_demo(payload.price_change_pct, payload.marketing_change_pct,
                             payload.horizon_days)
    sim_id = str(uuid.uuid4())
    record = Simulation(id=sim_id, dataset_id="demo", industry="retail",
                        inputs=payload.model_dump(), outputs=result)
    db.add(record)
    db.commit()
    return {"simulation_id": sim_id, "industry": "retail", **result}

@app.get("/api/v1/simulations")
def list_simulations(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(Simulation).order_by(Simulation.created_at.desc()).limit(min(max(limit, 1), 100)).all()
    return [{"simulation_id": r.id, "industry": r.industry, "inputs": r.inputs,
             "outputs": r.outputs, "created_at": r.created_at.isoformat()} for r in rows]


@app.post("/api/v1/ml/train")
def train_retail_model():
    from .ml_service import train_model
    try:
        return {"status": "trained", **train_model()}
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Model training failed: {exc}")

@app.get("/api/v1/ml/model")
def retail_model_metrics():
    from .ml_service import get_model_metrics
    try:
        return get_model_metrics()
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc))

@app.post("/api/v1/ml/forecast")
def retail_sales_forecast(horizon_days: int = 30):
    from .ml_service import forecast_sales
    try:
        return forecast_sales(horizon_days)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
