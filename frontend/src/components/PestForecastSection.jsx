import { useEffect, useState } from 'react'
import { pestForecastApi } from '../services/api'

const CROP_PEST_MAP = {
  Maize: 'Fall armyworm',
  Rice: 'Brown planthopper',
  Cotton: 'Pink bollworm',
  Wheat: 'Aphids',
  Tomato: 'Fruit borer',
  Chickpea: 'Pod borer',
}

const GROWTH_STAGES_BY_CROP = {
  Maize: ['V1_V4_early_whorl', 'V5_V8_mid_whorl', 'V9_VT_late_whorl', 'R1_silking', 'R2_R4_grain_fill', 'R5_R6_maturity'],
  Rice: ['Seedling_transplanting', 'Active_tillering', 'Panicle_initiation', 'Booting_heading', 'Milky_dough', 'Ripening_maturity'],
  Cotton: ['Vegetative', 'Squaring_bud', 'Flowering', 'Boll_formation', 'Boll_maturation', 'Bursting_picking'],
  Wheat: ['Crown_root_initiation', 'Tillering', 'Jointing_stem_extension', 'Booting_heading', 'Milky_grain', 'Dough_maturity'],
  Tomato: ['Vegetative_branching', 'Flowering', 'Fruit_setting', 'Fruit_development', 'Harvest_ripening'],
  Chickpea: ['Seedling', 'Vegetative_branching', 'Flowering', 'Early_pod_formation', 'Pod_filling', 'Maturity_senescence'],
}

const DISTRICTS = [
  'Davanagere', 'Belagavi', 'Chhindwara', 'Nagpur', 'Amravati',
  'East Godavari', 'Thanjavur', 'Ludhiana', 'Karnal', 'Kolar',
  'Nashik', 'Pune', 'Kalaburagi', 'Akola', 'Vidisha', 'Cuttack',
]

const DEFAULT_FORM = {
  crop: 'Maize',
  pest: 'Fall armyworm',
  district: 'Davanagere',
  growth_stage: 'V5_V8_mid_whorl',
  model_type: 'full',
  t7_mean_temp_c: '28.5',
  t7_min_temp_c: '22.0',
  t7_max_temp_c: '35.0',
  t7_mean_rh_pct: '78.0',
  t7_high_rh_days: '3',
  t7_rainfall_mm: '35.0',
  t14_rainfall_mm: '65.0',
  current_incidence_pct_t0: '4.5',
  current_severity_pct_t0: '2.1',
  pest_present_t0: '1',
}

export default function PestForecastSection() {
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [catalog, setCatalog] = useState(null)

  useEffect(() => {
    pestForecastApi.info().then(setCatalog).catch(() => {})
  }, [])

  const handleCropChange = (e) => {
    const selectedCrop = e.target.value
    const matchedPest = CROP_PEST_MAP[selectedCrop] || 'Fall armyworm'
    const stages = GROWTH_STAGES_BY_CROP[selectedCrop] || []
    setFormData((prev) => ({
      ...prev,
      crop: selectedCrop,
      pest: matchedPest,
      growth_stage: stages[0] || 'Vegetative',
    }))
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handlePreFill = async () => {
    try {
      const example = await pestForecastApi.example()
      setFormData({
        crop: example.crop || 'Maize',
        pest: example.pest || 'Fall armyworm',
        district: example.district || 'Davanagere',
        growth_stage: example.growth_stage || 'V5_V8_mid_whorl',
        model_type: example.model_type || 'full',
        t7_mean_temp_c: String(example.t7_mean_temp_c ?? 28.5),
        t7_min_temp_c: String(example.t7_min_temp_c ?? 22.0),
        t7_max_temp_c: String(example.t7_max_temp_c ?? 35.0),
        t7_mean_rh_pct: String(example.t7_mean_rh_pct ?? 78.0),
        t7_high_rh_days: String(example.t7_high_rh_days ?? 3),
        t7_rainfall_mm: String(example.t7_rainfall_mm ?? 35.0),
        t14_rainfall_mm: String(example.t14_rainfall_mm ?? 65.0),
        current_incidence_pct_t0: String(example.current_incidence_pct_t0 ?? 4.5),
        current_severity_pct_t0: String(example.current_severity_pct_t0 ?? 2.1),
        pest_present_t0: String(example.pest_present_t0 ?? 1),
      })
      setError('')
    } catch {
      setFormData(DEFAULT_FORM)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    // Build payload with numeric conversions
    const payload = {
      crop: formData.crop,
      pest: formData.pest,
      district: formData.district,
      growth_stage: formData.growth_stage,
      model_type: formData.model_type,
      t7_mean_temp_c: Number(formData.t7_mean_temp_c),
      t7_min_temp_c: Number(formData.t7_min_temp_c),
      t7_max_temp_c: Number(formData.t7_max_temp_c),
      t7_mean_rh_pct: Number(formData.t7_mean_rh_pct),
      t7_high_rh_days: Number(formData.t7_high_rh_days),
      t7_rainfall_mm: Number(formData.t7_rainfall_mm),
      t14_rainfall_mm: Number(formData.t14_rainfall_mm),
    }

    if (formData.model_type === 'full') {
      payload.current_incidence_pct_t0 = Number(formData.current_incidence_pct_t0)
      payload.current_severity_pct_t0 = Number(formData.current_severity_pct_t0)
      payload.pest_present_t0 = Number(formData.pest_present_t0)
    } else if (formData.model_type === 'early_warning') {
      payload.pest_present_t0 = Number(formData.pest_present_t0)
    }

    try {
      const resp = await pestForecastApi.predict(payload)
      setResult(resp)
    } catch (err) {
      setError(err.message || 'Failed to generate pest forecast.')
    } finally {
      setLoading(false)
    }
  }

  const currentStages = GROWTH_STAGES_BY_CROP[formData.crop] || []

  return (
    <div className="content-grid" id="pest-forecast">
      <section className="form-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">7-Day Outbreak Forecasting Prototype</p>
            <h2>Simulated Field Pest Forecaster</h2>
          </div>
          <button type="button" className="secondary-button" onClick={handlePreFill}>
            📋 Pre-fill Sample Scenario
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Model Selection */}
          <div className="form-field" style={{ marginBottom: '1.25rem' }}>
            <label htmlFor="model_type">Select Forecasting Model</label>
            <select
              id="model_type"
              name="model_type"
              className="form-select"
              value={formData.model_type}
              onChange={handleChange}
            >
              <option value="full">Full-Feature Model (Scouting + Weather — Threshold: 0.72)</option>
              <option value="weather_crop">Weather & Crop Model (Macro / Zero Scouting — Threshold: 0.42)</option>
              <option value="early_warning">Binary Early-Warning Model (Trap Presence + Weather — Threshold: 0.56)</option>
            </select>
            <small>
              {formData.model_type === 'full' && 'Requires 14 features: weather, phenology, and in-field scouting damage/incidence.'}
              {formData.model_type === 'weather_crop' && 'Requires 11 features: microclimate and phenology only. No field scouting needed.'}
              {formData.model_type === 'early_warning' && 'Requires 12 features: microclimate and binary trap detection (presence/absence).'}
            </small>
          </div>

          <div className="field-grid">
            {/* Crop Selector */}
            <div className="form-field">
              <label htmlFor="crop">Target Crop</label>
              <select id="crop" name="crop" className="form-select" value={formData.crop} onChange={handleCropChange}>
                {Object.keys(CROP_PEST_MAP).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Target Pest (Auto-matched) */}
            <div className="form-field">
              <label htmlFor="pest">Target Pest Species</label>
              <input id="pest" name="pest" type="text" value={formData.pest} readOnly style={{ background: '#f5f5f0', cursor: 'not-allowed' }} />
              <small>Auto-selected based on crop host biology</small>
            </div>

            {/* District */}
            <div className="form-field">
              <label htmlFor="district">Agricultural District</label>
              <select id="district" name="district" className="form-select" value={formData.district} onChange={handleChange}>
                {DISTRICTS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            {/* Growth Stage */}
            <div className="form-field">
              <label htmlFor="growth_stage">Phenological Growth Stage</label>
              <select id="growth_stage" name="growth_stage" className="form-select" value={formData.growth_stage} onChange={handleChange}>
                {currentStages.map((stg) => (
                  <option key={stg} value={stg}>{stg.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>
          </div>

          <h3 style={{ marginTop: '1.5rem', marginBottom: '0.8rem', color: '#173a2c' }}>
            🌤️ Antecedent Weather Profile (Past 7–14 Days at t₀)
          </h3>
          <div className="field-grid">
            <div className="form-field">
              <label htmlFor="t7_mean_temp_c">7-Day Mean Temperature (°C)</label>
              <input id="t7_mean_temp_c" name="t7_mean_temp_c" type="number" step="0.1" value={formData.t7_mean_temp_c} onChange={handleChange} required />
            </div>

            <div className="form-field">
              <label htmlFor="t7_min_temp_c">7-Day Min Temperature (°C)</label>
              <input id="t7_min_temp_c" name="t7_min_temp_c" type="number" step="0.1" value={formData.t7_min_temp_c} onChange={handleChange} required />
            </div>

            <div className="form-field">
              <label htmlFor="t7_max_temp_c">7-Day Max Temperature (°C)</label>
              <input id="t7_max_temp_c" name="t7_max_temp_c" type="number" step="0.1" value={formData.t7_max_temp_c} onChange={handleChange} required />
            </div>

            <div className="form-field">
              <label htmlFor="t7_mean_rh_pct">7-Day Mean Relative Humidity (%)</label>
              <input id="t7_mean_rh_pct" name="t7_mean_rh_pct" type="number" step="0.1" min="0" max="100" value={formData.t7_mean_rh_pct} onChange={handleChange} required />
            </div>

            <div className="form-field">
              <label htmlFor="t7_high_rh_days">High Humidity Days (RH ≥ 80%)</label>
              <input id="t7_high_rh_days" name="t7_high_rh_days" type="number" step="1" min="0" max="7" value={formData.t7_high_rh_days} onChange={handleChange} required />
              <small>Days in past week with RH ≥ 80%</small>
            </div>

            <div className="form-field">
              <label htmlFor="t7_rainfall_mm">7-Day Rainfall (mm)</label>
              <input id="t7_rainfall_mm" name="t7_rainfall_mm" type="number" step="0.1" min="0" value={formData.t7_rainfall_mm} onChange={handleChange} required />
            </div>

            <div className="form-field">
              <label htmlFor="t14_rainfall_mm">14-Day Rainfall (mm)</label>
              <input id="t14_rainfall_mm" name="t14_rainfall_mm" type="number" step="0.1" min="0" value={formData.t14_rainfall_mm} onChange={handleChange} required />
              <small>Must be ≥ 7-day cumulative rainfall</small>
            </div>
          </div>

          {/* Infestation Inputs (Conditional per model) */}
          {formData.model_type === 'full' && (
            <>
              <h3 style={{ marginTop: '1.5rem', marginBottom: '0.8rem', color: '#173a2c' }}>
                🔍 Field Scouting & Infestation State at t₀
              </h3>
              <div className="field-grid">
                <div className="form-field">
                  <label htmlFor="current_incidence_pct_t0">Current Infestation Incidence (%)</label>
                  <input id="current_incidence_pct_t0" name="current_incidence_pct_t0" type="number" step="0.1" min="0" max="100" value={formData.current_incidence_pct_t0} onChange={handleChange} required />
                  <small>% of scouted plants harboring insects/symptoms</small>
                </div>

                <div className="form-field">
                  <label htmlFor="current_severity_pct_t0">Current Damage Severity (%)</label>
                  <input id="current_severity_pct_t0" name="current_severity_pct_t0" type="number" step="0.1" min="0" max="100" value={formData.current_severity_pct_t0} onChange={handleChange} required />
                  <small>% foliar or fruit tissue loss observed</small>
                </div>

                <div className="form-field">
                  <label htmlFor="pest_present_t0">Pest Observable at t₀?</label>
                  <select id="pest_present_t0" name="pest_present_t0" className="form-select" value={formData.pest_present_t0} onChange={handleChange}>
                    <option value="1">Yes (Pests or fresh damage present)</option>
                    <option value="0">No (Zero observable pests)</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {formData.model_type === 'early_warning' && (
            <>
              <h3 style={{ marginTop: '1.5rem', marginBottom: '0.8rem', color: '#173a2c' }}>
                🪤 Binary Trap & Early Detection at t₀
              </h3>
              <div className="field-grid">
                <div className="form-field">
                  <label htmlFor="pest_present_t0">Pest Trap Catch / Activity Detected?</label>
                  <select id="pest_present_t0" name="pest_present_t0" className="form-select" value={formData.pest_present_t0} onChange={handleChange}>
                    <option value="1">Yes (Pheromone / light trap catch active)</option>
                    <option value="0">No (Zero trap detections)</option>
                  </select>
                  <small>Foliar scouting (% damage) is not required for this model.</small>
                </div>
              </div>
            </>
          )}

          {formData.model_type === 'weather_crop' && (
            <div style={{ marginTop: '1.2rem', padding: '0.8rem 1rem', background: '#f0f7ee', border: '1px solid #cce5c5', borderRadius: '8px', fontSize: '0.84rem', color: '#27522d' }}>
              ℹ️ <strong>Macro Forecasting Mode:</strong> Evaluates regional outbreak risk strictly from microclimatic humidity, temperature, and crop vulnerability. Does not require scouting or trap telemetry.
            </div>
          )}

          {error && (
            <div className="request-error" role="alert">
              <p><strong>Error:</strong> {error}</p>
            </div>
          )}

          <button type="submit" className="primary-button" disabled={loading} style={{ width: '100%' }}>
            {loading ? 'Simulating 7-Day Outbreak Risk...' : 'Forecast Outbreak Risk (Next 7 Days)'}
          </button>
        </form>
      </section>

      {/* Prediction Output Display */}
      <aside>
        {result ? (
          <div className="result-card">
            <p className="eyebrow">7-Day Forecast Evaluation</p>
            <h2 style={{ fontSize: '2rem', margin: '0.2rem 0' }}>
              {result.crop} — {result.target_pest}
            </h2>
            <p className="muted">Forecast Horizon: <strong>7 Days forward</strong></p>

            {/* Risk Badge */}
            <div className={`pest-risk-badge ${result.outbreak_predicted ? 'risk-high' : 'risk-low'}`} style={{ marginTop: '1rem' }}>
              <div className="badge-header">
                <strong>{result.outbreak_predicted ? '⚠️ HIGH OUTBREAK RISK' : '✅ LOW / NORMAL RISK'}</strong>
                <span>{(result.outbreak_probability * 100).toFixed(1)}%</span>
              </div>
              <p className="pest-threat">
                {result.outbreak_predicted
                  ? 'Simulated model conditions indicate elevated outbreak risk within the next 7 days.'
                  : 'Simulated model conditions indicate outbreak probability remains below the warning threshold for the next 7 days.'}
              </p>
              <div style={{ background: 'rgba(0,0,0,0.25)', height: '10px', borderRadius: '5px', overflow: 'hidden', marginTop: '0.75rem' }}>
                <div
                  style={{
                    width: `${Math.min(100, result.outbreak_probability * 100)}%`,
                    height: '100%',
                    background: result.outbreak_predicted ? '#ff4d4f' : '#52c41a',
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', marginTop: '0.3rem', opacity: 0.85 }}>
                <span>Probability: {(result.outbreak_probability * 100).toFixed(1)}%</span>
                <span>Decision Threshold: {(result.decision_threshold * 100).toFixed(0)}%</span>
              </div>
            </div>

            {/* Technical Metadata */}
            <div className="commercial-bags-card" style={{ marginTop: '1rem' }}>
              <h3>Forecast Configuration</h3>
              <div className="bags-list">
                <div className="bag-row">
                  <span>Model Architecture</span>
                  <strong>{result.model_label}</strong>
                </div>
                <div className="bag-row">
                  <span>Features Evaluated</span>
                  <strong>{result.features_used.length} Features</strong>
                </div>
                <div className="bag-row">
                  <span>Forecast Window</span>
                  <strong>Next 7 Calendar Days</strong>
                </div>
                <div className="bag-row">
                  <span>Target Threshold</span>
                  <strong>Economic Threshold Level (ETL)</strong>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-result">
            <h3>Pest Outbreak Early Warning</h3>
            <p>
              Select a crop, growth stage, and antecedent weather conditions to simulate a 7-day pest outbreak forecast.
            </p>
            <p style={{ fontSize: '0.82rem', color: '#687a6f', marginTop: '0.8rem' }}>
              <strong>Supported Crop-Pest Pairs:</strong>
              <br />• Maize — Fall armyworm
              <br />• Rice — Brown planthopper
              <br />• Cotton — Pink bollworm
              <br />• Wheat — Aphids
              <br />• Tomato — Fruit borer
              <br />• Chickpea — Pod borer
            </p>
          </div>
        )}
      </aside>
    </div>
  )
}
