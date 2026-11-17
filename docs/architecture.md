# Architecture and multi-industry design

## Request flow
React UI -> FastAPI -> validation/service layer -> industry adapter -> analytics/ML/simulation -> PostgreSQL.

## Multi-industry strategy
Keep a shared core data contract and use adapters for domain-specific semantics:
- `retail`: price, promotion, units, inventory, revenue.
- `energy`: load, tariff, weather, capacity.
- `education`: cohort, engagement, assessment, learning outcome.
- `healthcare`: only properly governed, de-identified operational data; avoid clinical recommendations in this MVP.

Do not assume a price-change field has meaning in every industry. Each adapter must define:
1. Required columns and units.
2. Target variable.
3. Valid scenario controls and ranges.
4. Forecast model and evaluation method.
5. Outcome calculations and constraints.

## Phase 1 boundary
The included what-if simulator is a retail demonstration to prove the user flow. Multi-industry support is an architectural extension point, not a claim that one model works across all sectors.
