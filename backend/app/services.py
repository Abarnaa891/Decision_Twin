from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "demo_retail_sales.csv"

def load_demo():
    return pd.read_csv(DATA_PATH)

def profile_dataframe(df: pd.DataFrame) -> dict:
    numeric = df.select_dtypes(include="number")
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "missing_by_column": {k: int(v) for k, v in df.isna().sum().items()},
        "numeric_summary": numeric.describe().round(3).fillna(0).to_dict(),
        "correlation": numeric.corr(numeric_only=True).round(3).fillna(0).to_dict()
    }

def run_retail_demo(price_change_pct: float, marketing_change_pct: float, horizon_days: int) -> dict:
    df = load_demo()
    baseline_units = float(df["units_sold"].tail(30).mean() * horizon_days)
    baseline_price = float(df["unit_price"].mean())
    baseline_revenue = baseline_units * baseline_price

    # Explicit demo assumptions only; replace with a trained model in Phase 2.
    price_elasticity = -1.2
    marketing_elasticity = 0.25
    demand_multiplier = max(0.05, 1 + price_elasticity * price_change_pct / 100
                            + marketing_elasticity * marketing_change_pct / 100)
    scenario_units = baseline_units * demand_multiplier
    scenario_price = baseline_price * (1 + price_change_pct / 100)
    scenario_revenue = scenario_units * scenario_price
    change_pct = ((scenario_revenue / baseline_revenue) - 1) * 100 if baseline_revenue else 0

    return {
        "baseline_units": round(baseline_units, 2),
        "scenario_units": round(scenario_units, 2),
        "baseline_revenue": round(baseline_revenue, 2),
        "scenario_revenue": round(scenario_revenue, 2),
        "estimated_revenue_change_pct": round(change_pct, 2),
        "assumptions": [
            "Illustrative retail demo using a fixed price elasticity of -1.2.",
            "Marketing elasticity is assumed to be 0.25; it is not learned from this small demo dataset.",
            "The model assumes constant average unit price and stable operating conditions.",
            "This is not a causal estimate or a guaranteed business outcome."
        ]
    }
