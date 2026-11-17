import { useEffect, useState } from 'react'
import { pestForecastingApi } from '../services/api'

const CROPS = ['Cotton', 'Rice', 'Maize', 'Soybean', 'Wheat', 'Tomato', 'Chickpea']
const DISTRICTS = ['Nagpur', 'Amravati', 'Yavatmal', 'Jalgaon', 'Wardha']
const GROWTH_STAGES = ['Squaring', 'Vegetative', 'Flowering', 'Fruiting', 'Stem Elongation']

const PESTS_BY_CROP = {
  Cotton: ['Pink bollworm', 'American bollworm'],
  Rice: ['Brown planthopper', 'Yellow stem borer'],
  Maize: ['Fall armyworm'],
  Soybean: ['Tobacco caterpillar'],
  Wheat: ['Aphids', 'Rust'],
  Tomato: ['Fruit borer', 'Leaf miner'],
  Chickpea: ['Pod borer'],
}

export default function ExperimentalPestForecastingSection() {
  const [configuration, setConfiguration] = useState('ENVIRONMENTAL_ONLY')
  const [crop, setCrop] = useState('Cotton')
  const [pest, setPest] = useState('Pink bollworm')
  const [district, setDistrict] = useState('Nagpur')
  const [growthStage, setGrowthStage] = useState('Squaring')

  // 7-day Antecedent Environmental & Topsoil parameters
  const [t7MeanTemp, setT7MeanTemp] = useState('31.5')
  const [t7MinTemp, setT7MinTemp] = useState('26.2')
  const [t7MaxTemp, setT7MaxTemp] = useState('36.8')
  const [t7MeanRh, setT7MeanRh] = useState('78.4')
  const [t7Rainfall, setT7Rainfall] = useState('12.5')
  const [t14Rainfall, setT14Rainfall] = useState('45.0')
  const [t7SoilMoisture, setT7SoilMoisture] = useState('0.385')
  const [t7HighRhDays, setT7HighRhDays] = useState('4')
  const [t7DryDays, setT7DryDays] = useState('2')

  // Scouting parameters
  const [scoutIncidence, setScoutIncidence] = useState('14.5')
  const [scoutSeverity, setScoutSeverity] = useState('8.0')
  const [trapCatch, setTrapCatch] = useState('18')
  const [daysSinceScouting, setDaysSinceScouting] = useState('3')
  const [pestPresent, setPestPresent] = useState(1)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [modelInfo, setModelInfo] = useState(null)

  // Fetch model metadata on mount
  useEffect(() => {
    pestForecastingApi.modelInfo()
      .then(info => setModelInfo(info))
      .catch(() => {})
  }, [])

  // Sync pest species when crop changes
  const handleCropChange = (e) => {
    const newCrop = e.target.value
    setCrop(newCrop)
    const available = PESTS_BY_CROP[newCrop] || ['General Pest']
    setPest(available[0])
  }

  // Load verified sample scenario
  const handleLoadExample = async (cfg) => {
    setError('')
    try {
      const ex = await pestForecastingApi.example(cfg)
      setConfiguration(ex.configuration || cfg)
      if (ex.crop) setCrop(ex.crop)
      if (ex.pest) setPest(ex.pest)
      if (ex.district) setDistrict(ex.district)
      if (ex.growth_stage) setGrowthStage(ex.growth_stage)
      if (ex.t7_mean_temp_c != null) setT7MeanTemp(String(ex.t7_mean_temp_c))
      if (ex.t7_min_temp_c != null) setT7MinTemp(String(ex.t7_min_temp_c))
      if (ex.t7_max_temp_c != null) setT7MaxTemp(String(ex.t7_max_temp_c))
      if (ex.t7_mean_rh_pct != null) setT7MeanRh(String(ex.t7_mean_rh_pct))
      if (ex.t7_rainfall_mm != null) setT7Rainfall(String(ex.t7_rainfall_mm))
      if (ex.t14_rainfall_mm != null) setT14Rainfall(String(ex.t14_rainfall_mm))
      if (ex.t7_mean_soil_moisture != null) setT7SoilMoisture(String(ex.t7_mean_soil_moisture))
      if (ex.t7_high_rh_days != null) setT7HighRhDays(String(ex.t7_high_rh_days))
      if (ex.t7_consecutive_dry_days != null) setT7DryDays(String(ex.t7_consecutive_dry_days))

      if (cfg === 'SCOUTING_ASSISTED') {
        if (ex.scout_incidence_pct != null) setScoutIncidence(String(ex.scout_incidence_pct))
        if (ex.scout_severity_pct != null) setScoutSeverity(String(ex.scout_severity_pct))
        if (ex.trap_catch_count != null) setTrapCatch(String(ex.trap_catch_count))
        if (ex.days_since_scouting != null) setDaysSinceScouting(String(ex.days_since_scouting))
        if (ex.pest_present != null) setPestPresent(ex.pest_present)
      }
    } catch (err) {
      setError('Could not load example scenario.')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    const minT = Number(t7MinTemp)
    const maxT = Number(t7MaxTemp)
    const r7 = Number(t7Rainfall)
    const r14 = Number(t14Rainfall)

    if (minT > maxT) {
      setError('Minimum temperature cannot exceed maximum temperature.')
      setLoading(false)
      return
    }
    if (r7 > r14) {
      setError('7-day cumulative rainfall cannot exceed 14-day cumulative rainfall.')
      setLoading(false)
      return
    }

    const payload = {
      configuration,
      crop,
      pest,
      district,
      growth_stage: growthStage,
      t7_mean_temp_c: Number(t7MeanTemp),
      t7_min_temp_c: minT,
      t7_max_temp_c: maxT,
      t7_mean_rh_pct: Number(t7MeanRh),
      t7_rainfall_mm: r7,
      t14_rainfall_mm: r14,
      t7_mean_soil_moisture: Number(t7SoilMoisture),
      t7_high_rh_days: parseInt(t7HighRhDays, 10),
      t7_consecutive_dry_days: parseInt(t7DryDays, 10),
    }

    if (configuration === 'SCOUTING_ASSISTED') {
      payload.scout_incidence_pct = Number(scoutIncidence)
      payload.scout_severity_pct = Number(scoutSeverity)
      payload.trap_catch_count = Number(trapCatch)
      payload.days_since_scouting = Number(daysSinceScouting)
      payload.pest_present = parseInt(pestPresent, 10)
    }

    try {
      const data = await pestForecastingApi.predict(payload)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Failed to generate experimental pest forecast.')
    } finally {
      setLoading(false)
    }
  }

  const probPercent = result ? Math.round(result.outbreak_risk_probability * 100) : 0
  const threshPercent = result ? Math.round(result.decision_threshold * 100) : 32

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Prominent Synthetic Experimental Disclaimer Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)',
        border: '1.5px solid #F59E0B',
        borderRadius: '14px',
        padding: '1.25rem 1.6rem',
        boxShadow: '0 2px 8px rgba(245, 158, 11, 0.12)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.45rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '1.4rem' }}>🔬</span>
          <strong style={{ color: '#B45309', fontSize: '1.05rem', letterSpacing: '0.02em', textTransform: 'uppercase' }}>
            Experimental 7-Day Pest Outbreak Forecaster (Version 2.0)
          </strong>
          <span style={{
            background: '#F59E0B',
            color: '#FFFFFF',
            fontSize: '0.725rem',
            fontWeight: 800,
            padding: '3px 9px',
            borderRadius: '6px',
            letterSpacing: '0.05em',
          }}>
            SYNTHETIC_EXPERIMENTAL
          </span>
          <span style={{
            background: '#EF4444',
            color: '#FFFFFF',
            fontSize: '0.725rem',
            fontWeight: 800,
            padding: '3px 9px',
            borderRadius: '6px',
            letterSpacing: '0.05em',
          }}>
            PRODUCTION BLOCKED
          </span>
        </div>
        <p style={{ margin: 0, fontSize: '0.85rem', color: '#78350F', lineHeight: 1.55 }}>
          <strong>SCIENTIFIC INVARIANT:</strong> This forecast is powered by machine learning pipelines trained exclusively on biophysical simulation datasets (Phase 21).
          Predictions are <em>strictly experimental</em> and must <strong>never</strong> be used for commercial pesticide spraying or farm operations.
          Production deployment remains blocked by the Scientific Readiness Gate until &ge;500 verified field surveillance records are acquired.
        </p>
      </div>

      {/* Main Grid: Inputs Panel & Results Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(350px, 450px) 1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Form Panel */}
        <section className="modern-card" style={{ padding: '1.5rem', border: '1.5px solid #CBD5BF' }}>
          <div style={{ marginBottom: '1.15rem', borderBottom: '1px solid #E2E8D8', paddingBottom: '0.75rem' }}>
            <p style={{ color: '#059669', fontSize: '0.75rem', fontWeight: 800, margin: '0 0 0.25rem 0', textTransform: 'uppercase' }}>
              Feature Pipeline Selection
            </p>
            <h3 style={{ margin: 0, color: '#13241B', fontSize: '1.25rem', fontWeight: 800 }}>Model Inference Setup</h3>
          </div>

          {/* Configuration Mode Selector */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <button
              type="button"
              onClick={() => { setConfiguration('ENVIRONMENTAL_ONLY'); setResult(null); }}
              style={{
                flex: 1,
                padding: '0.65rem 0.75rem',
                fontSize: '0.775rem',
                fontWeight: 700,
                borderRadius: '8px',
                cursor: 'pointer',
                border: configuration === 'ENVIRONMENTAL_ONLY' ? '2px solid #059669' : '1px solid #D1D5DB',
                background: configuration === 'ENVIRONMENTAL_ONLY' ? '#ECFDF5' : '#FFFFFF',
                color: configuration === 'ENVIRONMENTAL_ONLY' ? '#065F46' : '#4B5563',
                transition: 'all 0.15s ease',
              }}
            >
              🌱 Environmental Only
            </button>
            <button
              type="button"
              onClick={() => { setConfiguration('SCOUTING_ASSISTED'); setResult(null); }}
              style={{
                flex: 1,
                padding: '0.65rem 0.75rem',
                fontSize: '0.775rem',
                fontWeight: 700,
                borderRadius: '8px',
                cursor: 'pointer',
                border: configuration === 'SCOUTING_ASSISTED' ? '2px solid #059669' : '1px solid #D1D5DB',
                background: configuration === 'SCOUTING_ASSISTED' ? '#ECFDF5' : '#FFFFFF',
                color: configuration === 'SCOUTING_ASSISTED' ? '#065F46' : '#4B5563',
                transition: 'all 0.15s ease',
              }}
            >
              🔍 Scouting Assisted
            </button>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.95rem' }}>
            {/* Crop & Pest */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label className="modern-label" htmlFor="fc-crop">Crop</label>
                <select id="fc-crop" value={crop} onChange={handleCropChange} className="modern-select">
                  {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="modern-label" htmlFor="fc-pest">Pest Species</label>
                <select id="fc-pest" value={pest} onChange={(e) => setPest(e.target.value)} className="modern-select">
                  {(PESTS_BY_CROP[crop] || ['General Pest']).map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
            </div>

            {/* District & Stage */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label className="modern-label" htmlFor="fc-district">District</label>
                <select id="fc-district" value={district} onChange={(e) => setDistrict(e.target.value)} className="modern-select">
                  {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div>
                <label className="modern-label" htmlFor="fc-stage">Growth Stage</label>
                <select id="fc-stage" value={growthStage} onChange={(e) => setGrowthStage(e.target.value)} className="modern-select">
                  {GROWTH_STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>

            {/* Temperatures */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
              <div>
                <label className="modern-label" htmlFor="fc-mean-temp">Mean T (°C)</label>
                <input id="fc-mean-temp" type="number" step="0.1" value={t7MeanTemp} onChange={(e) => setT7MeanTemp(e.target.value)} className="modern-input" required />
              </div>
              <div>
                <label className="modern-label" htmlFor="fc-min-temp">Min T (°C)</label>
                <input id="fc-min-temp" type="number" step="0.1" value={t7MinTemp} onChange={(e) => setT7MinTemp(e.target.value)} className="modern-input" required />
              </div>
              <div>
                <label className="modern-label" htmlFor="fc-max-temp">Max T (°C)</label>
                <input id="fc-max-temp" type="number" step="0.1" value={t7MaxTemp} onChange={(e) => setT7MaxTemp(e.target.value)} className="modern-input" required />
              </div>
            </div>

            {/* Humidity & Soil Moisture */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label className="modern-label" htmlFor="fc-mean-rh">Mean RH (%)</label>
                <input id="fc-mean-rh" type="number" step="0.1" min="0" max="100" value={t7MeanRh} onChange={(e) => setT7MeanRh(e.target.value)} className="modern-input" required />
              </div>
              <div>
                <label className="modern-label" htmlFor="fc-soil-moist">Topsoil Moisture (m³/m³)</label>
                <input id="fc-soil-moist" type="number" step="0.001" min="0" max="1" value={t7SoilMoisture} onChange={(e) => setT7SoilMoisture(e.target.value)} className="modern-input" required />
              </div>
            </div>

            {/* Rainfall 7d & 14d */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label className="modern-label" htmlFor="fc-rain7">7-Day Rain (mm)</label>
                <input id="fc-rain7" type="number" step="0.1" min="0" value={t7Rainfall} onChange={(e) => setT7Rainfall(e.target.value)} className="modern-input" required />
              </div>
              <div>
                <label className="modern-label" htmlFor="fc-rain14">14-Day Rain (mm)</label>
                <input id="fc-rain14" type="number" step="0.1" min="0" value={t14Rainfall} onChange={(e) => setT14Rainfall(e.target.value)} className="modern-input" required />
              </div>
            </div>

            {/* Dry Days & High RH Days */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label className="modern-label" htmlFor="fc-rh-days">Days RH &ge; 80% (0-7)</label>
                <input id="fc-rh-days" type="number" min="0" max="7" value={t7HighRhDays} onChange={(e) => setT7HighRhDays(e.target.value)} className="modern-input" required />
              </div>
              <div>
                <label className="modern-label" htmlFor="fc-dry-days">Consecutive Dry Days (0-7)</label>
                <input id="fc-dry-days" type="number" min="0" max="7" value={t7DryDays} onChange={(e) => setT7DryDays(e.target.value)} className="modern-input" required />
              </div>
            </div>

            {/* Scouting Inputs (Only if SCOUTING_ASSISTED) */}
            {configuration === 'SCOUTING_ASSISTED' && (
              <div style={{
                background: '#FAFBF6',
                border: '1.5px solid #CBD5BF',
                borderRadius: '10px',
                padding: '0.95rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                marginTop: '0.25rem',
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#059669', textTransform: 'uppercase' }}>
                  In-Field Scouting Observations (Required)
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                  <div>
                    <label className="modern-label" htmlFor="fc-scout-inc">Infested Plants (%)</label>
                    <input id="fc-scout-inc" type="number" step="0.1" min="0" max="100" value={scoutIncidence} onChange={(e) => setScoutIncidence(e.target.value)} className="modern-input" required />
                  </div>
                  <div>
                    <label className="modern-label" htmlFor="fc-scout-sev">Tissue Damage (%)</label>
                    <input id="fc-scout-sev" type="number" step="0.1" min="0" max="100" value={scoutSeverity} onChange={(e) => setScoutSeverity(e.target.value)} className="modern-input" required />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
                  <div>
                    <label className="modern-label" htmlFor="fc-trap">Trap Catch Count</label>
                    <input id="fc-trap" type="number" step="1" min="0" value={trapCatch} onChange={(e) => setTrapCatch(e.target.value)} className="modern-input" required />
                  </div>
                  <div>
                    <label className="modern-label" htmlFor="fc-scout-days">Days Since Scout</label>
                    <input id="fc-scout-days" type="number" step="1" min="0" value={daysSinceScouting} onChange={(e) => setDaysSinceScouting(e.target.value)} className="modern-input" required />
                  </div>
                  <div>
                    <label className="modern-label" htmlFor="fc-present">Pest Present</label>
                    <select id="fc-present" value={pestPresent} onChange={(e) => setPestPresent(Number(e.target.value))} className="modern-select">
                      <option value={1}>Yes (1)</option>
                      <option value={0}>No (0)</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Example Preset Button */}
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => handleLoadExample(configuration)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#059669',
                  fontSize: '0.775rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textDecoration: 'underline',
                  padding: 0,
                }}
              >
                📋 Load ICAR Field Sample Scenario
              </button>
            </div>

            {error && (
              <div style={{ padding: '0.75rem', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#B91C1C', fontSize: '0.8rem' }}>
                ⚠️ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary-emerald"
              style={{ padding: '0.85rem', width: '100%', fontSize: '0.95rem', marginTop: '0.5rem' }}
            >
              {loading ? 'Executing ML Inference...' : '⚡ Run 7-Day Outbreak Forecast →'}
            </button>
          </form>
        </section>

        {/* Prediction Results Display */}
        <section>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="modern-card" style={{
                border: result.outbreak_warning ? '2px solid #EF4444' : '2px solid #10B981',
                padding: '1.5rem',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
              }}>
                {/* Header row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.775rem', color: '#6B7D72', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
                      📍 {result.input_summary?.district} · {result.input_summary?.crop?.toUpperCase()}
                    </div>
                    <h2 style={{ margin: '0.2rem 0', color: '#111827', fontSize: '1.55rem', fontWeight: 800 }}>
                      {result.input_summary?.pest}
                    </h2>
                    <span style={{ fontSize: '0.8rem', color: '#4B5563' }}>
                      Stage: <strong>{result.input_summary?.growth_stage}</strong> · Pipeline: <strong>{result.feature_configuration}</strong>
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    {result.outbreak_warning ? (
                      <div style={{
                        background: '#EF4444',
                        color: '#FFFFFF',
                        fontWeight: 800,
                        padding: '6px 14px',
                        borderRadius: '8px',
                        fontSize: '0.85rem',
                        letterSpacing: '0.04em',
                        boxShadow: '0 2px 6px rgba(239, 68, 68, 0.25)',
                      }}>
                        🚨 OUTBREAK WARNING
                      </div>
                    ) : (
                      <div style={{
                        background: '#10B981',
                        color: '#FFFFFF',
                        fontWeight: 800,
                        padding: '6px 14px',
                        borderRadius: '8px',
                        fontSize: '0.85rem',
                        letterSpacing: '0.04em',
                      }}>
                        ✅ NORMAL RISK (BELOW THRESHOLD)
                      </div>
                    )}
                  </div>
                </div>

                {/* Probability Meter */}
                <div style={{
                  marginTop: '1.35rem',
                  padding: '1.15rem',
                  background: result.outbreak_warning ? '#FEF2F2' : '#ECFDF5',
                  border: result.outbreak_warning ? '1px solid #FECDD3' : '1px solid #A7F3D0',
                  borderRadius: '12px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                    <span style={{ color: '#374151', fontWeight: 600 }}>Predicted Outbreak Risk Probability (7-Day Horizon):</span>
                    <strong style={{ color: result.outbreak_warning ? '#DC2626' : '#059669', fontSize: '1.35rem', fontWeight: 800 }}>
                      {(result.outbreak_risk_probability * 100).toFixed(1)}%
                    </strong>
                  </div>

                  {/* Progress bar with threshold marker */}
                  <div style={{ position: 'relative', height: '14px', background: '#E5E7EB', borderRadius: '7px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${Math.min(100, probPercent)}%`,
                      height: '100%',
                      background: result.outbreak_warning ? '#EF4444' : '#10B981',
                      borderRadius: '7px',
                      transition: 'width 0.6s ease',
                    }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.45rem', fontSize: '0.725rem', color: '#6B7280', fontWeight: 600 }}>
                    <span>0% (Inhibiting)</span>
                    <span style={{ color: '#D97706', fontWeight: 700 }}>
                      Decision Threshold: {(result.decision_threshold * 100).toFixed(0)}%
                    </span>
                    <span>100% (Certain Outbreak)</span>
                  </div>
                </div>

                {/* Metadata & Governance Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem', marginTop: '1.25rem' }}>
                  <div style={{ background: '#FAFBF6', border: '1px solid #E2E8D8', borderRadius: '8px', padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.7rem', color: '#6B7D72', textTransform: 'uppercase', fontWeight: 700 }}>Model Algorithm</div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#13241B', marginTop: '0.15rem' }}>{result.model_family}</div>
                  </div>
                  <div style={{ background: '#FAFBF6', border: '1px solid #E2E8D8', borderRadius: '8px', padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.7rem', color: '#6B7D72', textTransform: 'uppercase', fontWeight: 700 }}>Model Version</div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#047857', marginTop: '0.15rem', wordBreak: 'break-all' }}>{result.model_version}</div>
                  </div>
                  <div style={{ background: '#FAFBF6', border: '1px solid #E2E8D8', borderRadius: '8px', padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.7rem', color: '#6B7D72', textTransform: 'uppercase', fontWeight: 700 }}>Target Tier</div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#D97706', marginTop: '0.15rem' }}>Experimental (Synthetic)</div>
                  </div>
                  <div style={{ background: '#FAFBF6', border: '1px solid #E2E8D8', borderRadius: '8px', padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.7rem', color: '#6B7D72', textTransform: 'uppercase', fontWeight: 700 }}>Production Ready</div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#EF4444', marginTop: '0.15rem' }}>NO (Blocked)</div>
                  </div>
                </div>

                {/* Scientific Disclaimer */}
                <div style={{ marginTop: '1.25rem', padding: '0.95rem', background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: '10px' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#92400E', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                    ⚠️ Mandatory Scientific Disclaimer
                  </div>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: '#78350F', lineHeight: 1.5 }}>
                    {result.disclaimer}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="modern-card" style={{
              border: '2px dashed #CBD5BF',
              padding: '3.5rem 2rem',
              textAlign: 'center',
              color: '#4B5563',
              background: '#FAFBF6',
            }}>
              <span style={{ fontSize: '3rem', display: 'block', marginBottom: '0.85rem' }}>⚡</span>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#13241B', fontSize: '1.35rem', fontWeight: 800 }}>
                Awaiting Experimental Forecast Execution
              </h3>
              <p style={{ margin: 0, fontSize: '0.925rem', maxWidth: '460px', marginInline: 'auto', lineHeight: 1.6 }}>
                Configure environmental and optional in-field scouting parameters on the left and click <strong>Run 7-Day Outbreak Forecast</strong> to execute live inference against registered Version 2.0 experimental model pipelines.
              </p>
              {modelInfo && (
                <div style={{ marginTop: '1.25rem', display: 'inline-flex', gap: '0.65rem', alignItems: 'center', fontSize: '0.775rem', background: '#FFFFFF', padding: '0.4rem 0.85rem', borderRadius: '8px', border: '1px solid #E2E8D8' }}>
                  <span>Active Model: <strong>{modelInfo.model_version}</strong></span>
                  <span>·</span>
                  <span>Threshold: <strong>{modelInfo.decision_thresholds?.environmental}</strong> (Env) / <strong>{modelInfo.decision_thresholds?.scouting_assisted}</strong> (Scout)</span>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
