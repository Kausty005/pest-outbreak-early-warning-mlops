import { useState } from 'react'
import { advisoryApi } from '../services/api'

export default function UnifiedAdvisorySection() {
  const [params, setParams] = useState({
    N: '80',
    P: '45',
    K: '40',
    temperature: '29.5',
    humidity: '76',
    ph: '6.5',
    rainfall: '140',
    state_name: 'Maharashtra',
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [advisory, setAdvisory] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setParams(prev => ({ ...prev, [name]: value }))
  }

  const handleTestCottonRisk = () => {
    setParams({
      N: '120',
      P: '50',
      K: '50',
      temperature: '31.5',
      humidity: '78',
      ph: '7.0',
      rainfall: '85',
      state_name: 'Maharashtra',
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = {
        N: Number(params.N),
        P: Number(params.P),
        K: Number(params.K),
        temperature: Number(params.temperature),
        humidity: Number(params.humidity),
        ph: Number(params.ph),
        rainfall: Number(params.rainfall),
        state_name: params.state_name,
      }
      const data = await advisoryApi.unified(payload)
      setAdvisory(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="unified-advisory-container" id="unified-advisory">
      <div className="section-header">
        <div>
          <p className="eyebrow">End-to-End MLOps Pipeline</p>
          <h2>Unified Agricultural Advisory & Pest Early-Warning</h2>
          <p className="muted">
            Seamlessly orchestrates Crop Selection, Fertilizer Optimization, and Pest Outbreak Risk Screening.
          </p>
        </div>
        <button type="button" className="secondary-button" onClick={handleTestCottonRisk}>
          Test Maharashtra Cotton Scenario
        </button>
      </div>

      <div className="content-grid">
        <section className="form-panel">
          <form onSubmit={handleSubmit}>
            <div className="field-grid">
              <div className="form-field">
                <label htmlFor="adv-n">Nitrogen (N)</label>
                <input id="adv-n" name="N" type="number" step="any" value={params.N} onChange={handleChange} required />
                <small>Soil Nitrogen reading</small>
              </div>
              <div className="form-field">
                <label htmlFor="adv-p">Phosphorus (P)</label>
                <input id="adv-p" name="P" type="number" step="any" value={params.P} onChange={handleChange} required />
                <small>Soil Phosphorus reading</small>
              </div>
              <div className="form-field">
                <label htmlFor="adv-k">Potassium (K)</label>
                <input id="adv-k" name="K" type="number" step="any" value={params.K} onChange={handleChange} required />
                <small>Soil Potassium reading</small>
              </div>
              <div className="form-field">
                <label htmlFor="adv-temp">Temperature (°C)</label>
                <input id="adv-temp" name="temperature" type="number" step="0.1" value={params.temperature} onChange={handleChange} required />
                <small>Ambient temperature</small>
              </div>
              <div className="form-field">
                <label htmlFor="adv-hum">Relative Humidity (%)</label>
                <input id="adv-hum" name="humidity" type="number" step="0.1" value={params.humidity} onChange={handleChange} required />
                <small>Hygrometric sensor reading</small>
              </div>
              <div className="form-field">
                <label htmlFor="adv-ph">Soil pH</label>
                <input id="adv-ph" name="ph" type="number" step="0.1" value={params.ph} onChange={handleChange} required />
                <small>0–14 pH scale</small>
              </div>
              <div className="form-field">
                <label htmlFor="adv-rain">Rainfall (mm)</label>
                <input id="adv-rain" name="rainfall" type="number" step="any" value={params.rainfall} onChange={handleChange} required />
                <small>Seasonal precipitation</small>
              </div>
              <div className="form-field">
                <label htmlFor="adv-state">State</label>
                <input id="adv-state" name="state_name" type="text" value={params.state_name} onChange={handleChange} required />
                <small>Regional location</small>
              </div>
            </div>

            {error && <div className="request-error" role="alert"><p>{error}</p></div>}

            <button type="submit" className="primary-button" disabled={loading}>
              {loading ? 'Evaluating Advisory Models...' : 'Run Full Agricultural Intelligence Advisory'}
            </button>
          </form>
        </section>

        <aside>
          {advisory ? (
            <div className="result-card advisory-card">
              <p className="eyebrow">Comprehensive Field Plan</p>
              <h2>{advisory.crop_recommendation.primary_crop}</h2>
              <p className="muted">Orchestrated across Crop & Fertilizer MLOps Pipelines</p>

              {/* Pest Early Warning Section */}
              <div className={`pest-risk-badge risk-${advisory.pest_early_warning_preview.preliminary_risk_level.toLowerCase()}`}>
                <div className="badge-header">
                  <span>🌾 Pest Outbreak Risk:</span>
                  <strong>{advisory.pest_early_warning_preview.preliminary_risk_level}</strong>
                </div>
                <p className="pest-threat">Target: {advisory.pest_early_warning_preview.primary_threat}</p>
                {advisory.pest_early_warning_preview.environmental_factors.map((factor, idx) => (
                  <p key={idx} className="pest-factor">• {factor}</p>
                ))}
                <small className="pest-note">{advisory.pest_early_warning_preview.next_phase_note}</small>
              </div>

              {/* Fertilizer Summary */}
              {advisory.fertilizer_advisory && (
                <div className="commercial-bags-card" style={{ marginTop: '1.2rem' }}>
                  <h3>Tailored Fertilizer Dosages ({advisory.fertilizer_advisory.crop})</h3>
                  <div className="bags-list">
                    <div className="bag-row">
                      <span>Urea (46% N)</span>
                      <strong>{advisory.fertilizer_advisory.fertilizer_commercial_equivalent_approx.urea_46_pct_n_kg_ha} kg/ha</strong>
                    </div>
                    <div className="bag-row">
                      <span>DAP (46% P₂O₅)</span>
                      <strong>{advisory.fertilizer_advisory.fertilizer_commercial_equivalent_approx.dap_46_pct_p2o5_kg_ha} kg/ha</strong>
                    </div>
                    <div className="bag-row">
                      <span>MOP (60% K₂O)</span>
                      <strong>{advisory.fertilizer_advisory.fertilizer_commercial_equivalent_approx.mop_60_pct_k2o_kg_ha} kg/ha</strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Guidance bullets */}
              <div className="advisory-box" style={{ marginTop: '1.2rem' }}>
                <h4>Field Guidance & Advisory Notes:</h4>
                <ul>
                  {advisory.field_guidance.map((note, idx) => (
                    <li key={idx} style={{ fontSize: '0.82rem', marginBottom: '0.3rem' }}>{note}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="empty-result">
              <p>Enter field sensor values and click <strong>Run Full Agricultural Intelligence Advisory</strong> to generate combined Crop Selection, Fertilizer Sizing, and Pest Outbreak Watchlist.</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
