from __future__ import annotations

from pathlib import Path
from datetime import timedelta
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "demo_retail_sales.csv"
MODEL_DIR = Path(__file__).resolve().parents[1] / "artifacts"
MODEL_PATH = MODEL_DIR / "retail_sales_model.joblib"
METRICS_PATH = MODEL_DIR / "retail_sales_metrics.json"

FEATURES = [
    "day_of_week", "day_of_month", "month", "day_of_year",
    "is_weekend", "promotion",
    "unit_price", "marketing_spend",
    "lag_1", "lag_7", "lag_14",
    "rolling_mean_7", "rolling_mean_14"
]

def load_retail_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    required = {"date", "units_sold", "unit_price", "promotion", "marketing_spend"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    for col in ["units_sold", "unit_price", "promotion", "marketing_spend"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "units_sold", "unit_price", "promotion", "marketing_spend"])
    if len(df) < 45:
        raise ValueError("At least 45 clean daily records are required for this starter model.")
    return df

def make_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy().sort_values("date").reset_index(drop=True)
    dates = x["date"]
    x["day_of_week"] = dates.dt.dayofweek
    x["day_of_month"] = dates.dt.day
    x["month"] = dates.dt.month
    x["day_of_year"] = dates.dt.dayofyear
    x["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)
    x["lag_1"] = x["units_sold"].shift(1)
    x["lag_7"] = x["units_sold"].shift(7)
    x["lag_14"] = x["units_sold"].shift(14)
    x["rolling_mean_7"] = x["units_sold"].shift(1).rolling(7).mean()
    x["rolling_mean_14"] = x["units_sold"].shift(1).rolling(14).mean()
    return x.dropna(subset=FEATURES + ["units_sold"]).reset_index(drop=True)

def train_model() -> dict:
    raw = load_retail_data()
    featured = make_features(raw)
    split = int(len(featured) * 0.80)
    train, test = featured.iloc[:split], featured.iloc[split:]
    if len(test) < 10:
        raise ValueError("Not enough holdout rows. Add more historical observations.")

    X_train, y_train = train[FEATURES], train["units_sold"]
    X_test, y_test = test[FEATURES], test["units_sold"]

    # Naive baseline: predict the training-set mean for every test day.
    baseline = DummyRegressor(strategy="mean")
    baseline.fit(X_train, y_train)
    baseline_pred = baseline.predict(X_test)

    model = RandomForestRegressor(
        n_estimators=350,
        max_depth=8,
        min_samples_leaf=2,
        max_features=0.9,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    predictions = np.maximum(0, model.predict(X_test))

    mae = float(mean_absolute_error(y_test, predictions))
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    baseline_mae = float(mean_absolute_error(y_test, baseline_pred))
    r2 = float(r2_score(y_test, predictions))

    # Refit on all available rows after honest chronological holdout evaluation.
    model.fit(featured[FEATURES], featured["units_sold"])
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES, "trained_through": raw["date"].max().isoformat()}, MODEL_PATH)

    metrics = {
        "model": "RandomForestRegressor",
        "target": "units_sold",
        "training_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_test_method": "Chronological 80/20 split; no random shuffling",
        "test_start_date": test["date"].min().date().isoformat(),
        "test_end_date": test["date"].max().date().isoformat(),
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "r2": round(r2, 3),
        "baseline_mae": round(baseline_mae, 3),
        "mae_improvement_vs_baseline_pct": round((baseline_mae - mae) / baseline_mae * 100, 2) if baseline_mae else None,
        "trained_through": raw["date"].max().date().isoformat(),
        "limitations": [
            "The bundled data is synthetic demonstration data, not real store transactions.",
            "The holdout period is small; metrics are educational and not production validation.",
            "Future price, promotion and marketing values are held at recent historical medians.",
            "Forecasts are predictive estimates, not causal estimates of business interventions."
        ]
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics

def get_model_metrics() -> dict:
    if not METRICS_PATH.exists() or not MODEL_PATH.exists():
        raise FileNotFoundError("No trained model found. Call POST /api/v1/ml/train first.")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

def forecast_sales(horizon_days: int = 30) -> dict:
    if not 1 <= horizon_days <= 90:
        raise ValueError("horizon_days must be between 1 and 90.")
    if not MODEL_PATH.exists():
        raise FileNotFoundError("No trained model found. Call POST /api/v1/ml/train first.")

    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    history = load_retail_data().copy().sort_values("date").reset_index(drop=True)
    last_date = history["date"].max()
    recent = history.tail(28)
    future_rows = []
    unit_price = float(recent["unit_price"].median())
    marketing = float(recent["marketing_spend"].median())
    promotion = int(recent["promotion"].mode().iloc[0]) if not recent["promotion"].mode().empty else 0

    values = history["units_sold"].astype(float).tolist()
    for step in range(1, horizon_days + 1):
        date = last_date + timedelta(days=step)
        row = {
            "day_of_week": date.dayofweek,
            "day_of_month": date.day,
            "month": date.month,
            "day_of_year": date.dayofyear,
            "is_weekend": int(date.dayofweek >= 5),
            "promotion": promotion,
            "unit_price": unit_price,
            "marketing_spend": marketing,
            "lag_1": values[-1],
            "lag_7": values[-7],
            "lag_14": values[-14],
            "rolling_mean_7": float(np.mean(values[-7:])),
            "rolling_mean_14": float(np.mean(values[-14:]))
        }
        pred = max(0.0, float(model.predict(pd.DataFrame([row])[FEATURES])[0]))
        values.append(pred)
        future_rows.append({"date": date.date().isoformat(), "predicted_units": round(pred, 2)})

    total = float(sum(x["predicted_units"] for x in future_rows))
    avg = total / horizon_days
    return {
        "model": "RandomForestRegressor",
        "horizon_days": horizon_days,
        "forecast_start": future_rows[0]["date"],
        "forecast_end": future_rows[-1]["date"],
        "predicted_total_units": round(total, 2),
        "predicted_average_daily_units": round(avg, 2),
        "daily_forecast": future_rows,
        "future_feature_assumptions": {
            "unit_price": round(unit_price, 2),
            "marketing_spend": round(marketing, 2),
            "promotion": promotion,
            "note": "Recent historical median/mode values are held constant for future exogenous features."
        },
        "warning": "Predictive forecast on synthetic demo data; not a causal scenario estimate."
    }
