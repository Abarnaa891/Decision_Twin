import { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export default function App() {
  const [profile, setProfile] = useState(null)
  const [price, setPrice] = useState(10)
  const [marketing, setMarketing] = useState(5)
  const [days, setDays] = useState(30)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [mlBusy, setMlBusy] = useState(false)
  const [mlError, setMlError] = useState('')
  const [modelMetrics, setModelMetrics] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [forecastDays, setForecastDays] = useState(30)

  useEffect(() => {
    fetch(`${API}/api/v1/datasets/demo/profile`)
      .then(r => { if (!r.ok) throw new Error('Could not load demo dataset'); return r.json() })
      .then(setProfile).catch(e => setError(e.message))
  }, [])

  async function simulate(e) {
    e.preventDefault(); setBusy(true); setError(''); setResult(null)
    try {
      const response = await fetch(`${API}/api/v1/simulations`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({dataset_id:'demo', industry:'retail',
          price_change_pct:Number(price), marketing_change_pct:Number(marketing),
          horizon_days:Number(days)})
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Simulation failed')
      setResult(data)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  async function trainModel() {
    setMlBusy(true); setMlError(''); setModelMetrics(null); setForecast(null)
    try {
      const response = await fetch(`${API}/api/v1/ml/train`, {method:'POST'})
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Model training failed')
      setModelMetrics(data)
    } catch (e) { setMlError(e.message) } finally { setMlBusy(false) }
  }

  async function runForecast() {
    setMlBusy(true); setMlError(''); setForecast(null)
    try {
      const response = await fetch(`${API}/api/v1/ml/forecast?horizon_days=${forecastDays}`, {method:'POST'})
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Forecast failed')
      setForecast(data)
    } catch (e) { setMlError(e.message) } finally { setMlBusy(false) }
  }

  const money = n => new Intl.NumberFormat('en-IN', {style:'currency', currency:'INR', maximumFractionDigits:0}).format(n)

  return <main className="shell">
    <header><div className="brandmark">DT</div><div><p className="eyebrow">DECISION INTELLIGENCE PLATFORM</p><h1>DecisionTwin <span>AI</span></h1></div><div className="status">● API-connected starter</div></header>
    <section className="hero"><div><p className="eyebrow">SEE THE POSSIBLE FUTURES</p><h2>Make decisions before<br/>they become reality.</h2><p className="sub">Explore business scenarios using data analysis and a transparent what-if simulation engine.</p></div><div className="hero-art">↗<small>DATA → MODEL → SCENARIO</small></div></section>
    {error && <div className="error">{error}</div>}
    <section className="grid">
      <article className="panel"><div className="panel-head"><div><p className="eyebrow">DATA FOUNDATION</p><h3>Demo dataset profile</h3></div><span className="tag">Retail demo</span></div>
        {profile ? <><div className="metrics"><div><strong>{profile.profile.rows.toLocaleString()}</strong><small>Rows</small></div><div><strong>{profile.profile.columns}</strong><small>Columns</small></div></div><p className="muted">Fields: {profile.profile.column_names.join(', ')}</p></> : <p className="muted">Loading dataset profile…</p>}
      </article>
      <article className="panel"><p className="eyebrow">WHAT-IF WORKSPACE</p><h3>Build a scenario</h3>
        <form onSubmit={simulate}>
          <label>Product price change <b>{price}%</b><input type="range" min="-20" max="30" value={price} onChange={e=>setPrice(e.target.value)}/></label>
          <label>Marketing budget change <b>{marketing}%</b><input type="range" min="-50" max="100" value={marketing} onChange={e=>setMarketing(e.target.value)}/></label>
          <label>Forecast horizon <b>{days} days</b><input type="range" min="7" max="90" step="1" value={days} onChange={e=>setDays(e.target.value)}/></label>
          <button disabled={busy}>{busy ? 'Simulating…' : 'Run scenario →'}</button>
        </form>
      </article>
    </section>
    <section className="panel result">
      <p className="eyebrow">PHASE 2 · MACHINE LEARNING</p>
      <h3>Retail sales forecasting</h3>
      <p className="muted">Train a Random Forest model on historical sales, inspect chronological holdout metrics, then forecast future daily units.</p>
      <div className="actions">
        <button onClick={trainModel} disabled={mlBusy}>{mlBusy ? 'Working…' : 'Train / evaluate model →'}</button>
        <label>Forecast days <b>{forecastDays}</b>
          <input type="range" min="7" max="90" value={forecastDays} onChange={e=>setForecastDays(Number(e.target.value))}/>
        </label>
        <button className="secondary" onClick={runForecast} disabled={mlBusy}>Generate forecast</button>
      </div>
      {mlError && <div className="error">{mlError}</div>}
      {modelMetrics && <><h4>Holdout evaluation</h4><div className="metrics four">
        <div><strong>{modelMetrics.mae}</strong><small>MAE · units/day</small></div>
        <div><strong>{modelMetrics.rmse}</strong><small>RMSE</small></div>
        <div><strong>{modelMetrics.r2}</strong><small>R²</small></div>
        <div><strong>{modelMetrics.baseline_mae}</strong><small>Baseline MAE</small></div>
      </div><p className="muted">Test window: {modelMetrics.test_start_date} to {modelMetrics.test_end_date}. MAE improvement vs baseline: {modelMetrics.mae_improvement_vs_baseline_pct}%.</p></>}
      {forecast && <><h4>{forecast.horizon_days}-day forecast</h4><div className="metrics">
        <div><strong>{forecast.predicted_total_units.toLocaleString()}</strong><small>Predicted total units</small></div>
        <div><strong>{forecast.predicted_average_daily_units.toLocaleString()}</strong><small>Average units/day</small></div>
      </div><div className="forecast-list">{forecast.daily_forecast.slice(0,14).map(day=><div key={day.date}><span>{day.date}</span><b>{day.predicted_units}</b></div>)}</div>
      <p className="muted">{forecast.warning}</p></>}
      <p className="muted">Evaluation uses a chronological 80/20 split. Forecast inputs hold recent price, marketing spend and promotion values constant. Synthetic demo data is for development, not business decisions.</p>
    </section>
    {result && <section className="panel result"><p className="eyebrow">SIMULATION RESULT · {result.simulation_id.slice(0,8)}</p><h3>Baseline vs scenario</h3><div className="metrics four"><div><strong>{money(result.baseline_revenue)}</strong><small>Baseline revenue</small></div><div><strong>{money(result.scenario_revenue)}</strong><small>Scenario revenue</small></div><div><strong>{result.estimated_revenue_change_pct}%</strong><small>Estimated change</small></div><div><strong>{result.scenario_units.toLocaleString()}</strong><small>Scenario units</small></div></div><h4>Assumptions and limitations</h4><ul>{result.assumptions.map(x=><li key={x}>{x}</li>)}</ul></section>}
    <footer>Phase 1 starter · Demo simulation uses explicit assumptions, not a trained causal model.</footer>
  </main>
}
