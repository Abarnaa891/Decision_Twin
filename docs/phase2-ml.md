# Phase 2 — Retail sales forecasting

## What is included
- A Random Forest regression model predicting daily `units_sold`.
- Calendar features, lag features (1/7/14 days), and rolling averages (7/14 days).
- Chronological 80/20 holdout evaluation; no random train/test shuffling.
- A constant-mean baseline for comparison.
- MAE, RMSE and R² metrics.
- Recursive 1–90 day forecasting endpoint.
- Model artifacts are generated locally under `backend/artifacts/` and are ignored by Git.

## Install
Activate the backend virtual environment and run:

```powershell
pip install -r requirements.txt
```

Restart FastAPI after installing.

## Train
In Swagger (`http://127.0.0.1:8000/docs`), call:

`POST /api/v1/ml/train`

Or in PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/ml/train
```

## Inspect evaluation
`GET /api/v1/ml/model`

The API returns the chronological test window, MAE, RMSE, R², and baseline MAE. MAE is in units sold per day. Compare model MAE with baseline MAE; a negative improvement means the model did worse than the simple baseline.

## Forecast
`POST /api/v1/ml/forecast?horizon_days=30`

PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/ml/forecast?horizon_days=30"
```

The future exogenous inputs (price, marketing spend and promotion) are held at recent historical median/mode values. The model is trained on synthetic demo data and is for learning, not operational decisions.

## Feature engineering
For each day t, features use only information available up to t-1:
- calendar: weekday, day, month, day of year, weekend
- exogenous: price, promotion, marketing spend
- lags: units at t-1, t-7, t-14
- rolling averages: previous 7 and 14 days

## Important modelling caveats
- This starter forecasts sales under historical-like inputs. It does not estimate the causal effect of price or marketing changes.
- Do not interpret feature importance as causal impact.
- Before production use, validate on a larger real dataset, compare seasonal/time-series baselines, monitor drift, and use prediction intervals.
- Retrain only after checking data quality and chronological evaluation.
