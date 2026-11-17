from pydantic import BaseModel, Field

class SimulationRequest(BaseModel):
    dataset_id: str = "demo"
    industry: str = "retail"
    price_change_pct: float = Field(default=0, ge=-80, le=300)
    marketing_change_pct: float = Field(default=0, ge=-100, le=500)
    horizon_days: int = Field(default=30, ge=1, le=365)

class SimulationResponse(BaseModel):
    simulation_id: str
    industry: str
    baseline_units: float
    scenario_units: float
    baseline_revenue: float
    scenario_revenue: float
    estimated_revenue_change_pct: float
    assumptions: list[str]
