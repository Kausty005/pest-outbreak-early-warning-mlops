import { useEffect, useState } from 'react'
import { pestRiskApi } from '../services/api'
import ExperimentalPestForecastingSection from './ExperimentalPestForecastingSection'

const DEFAULT_CROPS = ['cotton', 'soybean', 'rice', 'maize']
const DEFAULT_DISTRICTS = ['Nagpur', 'Amravati', 'Yavatmal', 'Jalgaon']

const PEST_MAPPING = {
  cotton: [
    { id: 'pink_bollworm', label: 'Pink Bollworm (Pectinophora gossypiella)' },
    { id: 'american_bollworm', label: 'American Bollworm (Helicoverpa armigera)' },
  ],
  soybean: [
    { id: 'tobacco_caterpillar', label: 'Tobacco Caterpillar (Spodoptera litura)' },
  ],
  rice: [
    { id: 'brown_planthopper', label: 'Brown Planthopper (Nilaparvata lugens)' },
  ],
  maize: [
    { id: 'fall_armyworm', label: 'Fall Armyworm (Spodoptera frugiperda)' },
  ],
}

export default function EnvironmentalPestRiskSection({ preselectedCrop }) {
  const [crop, setCrop] = useState(preselectedCrop ? preselectedCrop.toLowerCase() : 'cotton')
  const [pest, setPest] = useState('pink_bollworm')
  const [district, setDistrict] = useState('Nagpur')
  const [assessmentDate, setAssessmentDate] = useState('2023-09-15')
  const [plantingDate, setPlantingDate] = useState('2023-06-15')
  const [fetchLiveForecast, setFetchLiveForecast] = useState(false)
  const [engineMode, setEngineMode] = useState('biophysical') // 'biophysical' or 'ml-forecasting'

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (preselectedCrop) {
      const lower = preselectedCrop.toLowerCase()
      if (PEST_MAPPING[lower]) {
        setCrop(lower)
        setPest(PEST_MAPPING[lower][0].id)
      }
    }
  }, [preselectedCrop])

  // Update available pests when crop changes
  const handleCropChange = (e) => {
    const newCrop = e.target.value
    setCrop(newCrop)
    const availablePests = PEST_MAPPING[newCrop] || []
    if (availablePests.length > 0) {
      setPest(availablePests[0].id)
    } else {
      setPest('')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = {
        crop,
        pest: pest || undefined,
        district,
        assessment_date: assessmentDate || undefined,
        planting_date: plantingDate || undefined,
        fetch_live_forecast: fetchLiveForecast,
      }
      const data = await pestRiskApi.assess(payload)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Failed to evaluate pest favorability.')
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (cat) => {
    switch (cat) {
      case 'HIGH': return '#DC2626'
      case 'MODERATE': return '#D97706'
      case 'LOW': return '#059669'
      default: return '#64748B'
    }
  }

  const getRiskBg = (cat) => {
    switch (cat) {
      case 'HIGH': return '#FEF2F2'
      case 'MODERATE': return '#FFFBEB'
      case 'LOW': return '#ECFDF5'
      default: return '#F8FAFC'
    }
  }

  const getTrendBadge = (trend) => {
    switch (trend) {
      case 'RISING': return { label: '↗ RISING RISK', color: '#DC2626', bg: '#FEE2E2', border: '#FCA5A5' }
      case 'DECLINING': return { label: '↘ DECLINING RISK', color: '#059669', bg: '#D1FAE5', border: '#6EE7B7' }
      case 'STABLE': return { label: '→ STABLE', color: '#0284C7', bg: '#E0F2FE', border: '#7DD3FC' }
      default: return { label: '• HISTORICAL ONLY', color: '#475569', bg: '#F1F5F9', border: '#CBD5E1' }
    }
  }

  return (
    <div className="environmental-pest-risk-container" id="pest-risk-section" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Prominent Experimental Disclaimer Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)',
        border: '1.5px solid #F59E0B',
        borderRadius: '14px',
        padding: '1.2rem 1.6rem',
        boxShadow: '0 2px 8px rgba(245, 158, 11, 0.12)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.45rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '1.4rem' }}>🔬</span>
          <strong style={{ color: '#B45309', fontSize: '1.05rem', letterSpacing: '0.02em', textTransform: 'uppercase' }}>
            Biophysical Pest Outbreak & Favorability Surveillance Engine
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
            TIER 1 MACRO-CLIMATIC
          </span>
        </div>
        <p style={{ margin: 0, fontSize: '0.875rem', color: '#78350F', lineHeight: 1.55 }}>
          This biophysical engine calculates environmental favorability from aligned ERA5 topsoil and IMD/Open-Meteo microclimatic observations.
          It isolates ambient conditions conducive to pest egg incubation and fungal sporulation without confusing advisories with raw field measurements.
        </p>
      </div>

      {/* Engine Mode Selector */}
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
        <button
          type="button"
          onClick={() => setEngineMode('biophysical')}
          style={{
            padding: '0.55rem 1.15rem',
            borderRadius: '10px',
            fontSize: '0.825rem',
            fontWeight: 800,
            cursor: 'pointer',
            border: engineMode === 'biophysical' ? '2px solid #059669' : '1px solid #CBD5BF',
            background: engineMode === 'biophysical' ? '#ECFDF5' : '#FFFFFF',
            color: engineMode === 'biophysical' ? '#065F46' : '#4B5563',
            transition: 'all 0.15s ease',
          }}
        >
          🔬 ICAR Biophysical Favorability (Rule-Based EFI)
        </button>
        <button
          type="button"
          onClick={() => setEngineMode('ml-forecasting')}
          style={{
            padding: '0.55rem 1.15rem',
            borderRadius: '10px',
            fontSize: '0.825rem',
            fontWeight: 800,
            cursor: 'pointer',
            border: engineMode === 'ml-forecasting' ? '2px solid #059669' : '1px solid #CBD5BF',
            background: engineMode === 'ml-forecasting' ? '#ECFDF5' : '#FFFFFF',
            color: engineMode === 'ml-forecasting' ? '#065F46' : '#4B5563',
            transition: 'all 0.15s ease',
          }}
        >
          ⚡ Experimental ML Outbreak Forecasting (v2.0)
        </button>
      </div>

      {engineMode === 'ml-forecasting' ? (
        <ExperimentalPestForecastingSection />
      ) : (
        <div className="content-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 420px) 1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Input Parameters Panel */}
        <section className="modern-card" style={{ padding: '1.5rem' }}>
          <div style={{ marginBottom: '1.25rem', borderBottom: '1px solid #E2E8D8', paddingBottom: '0.85rem' }}>
            <p style={{ color: '#059669', fontSize: '0.75rem', fontWeight: 800, margin: '0 0 0.35rem 0', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              🌾 Biophysical Parameter Screening
            </p>
            <h3 style={{ margin: 0, color: '#13241B', fontSize: '1.25rem', fontWeight: 800 }}>Configure Pest Assessment</h3>
            <p style={{ fontSize: '0.825rem', color: '#4B5563', margin: '0.25rem 0 0 0' }}>
              Select target crop, pest, and Maharashtra district.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
              <div>
                <label className="modern-label" htmlFor="pest-crop">Target Crop</label>
                <select
                  id="pest-crop"
                  value={crop}
                  onChange={handleCropChange}
                  className="modern-select"
                >
                  {DEFAULT_CROPS.map(c => (
                    <option key={c} value={c}>
                      {c.charAt(0).toUpperCase() + c.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="modern-label" htmlFor="pest-species">Target Pest Species</label>
                <select
                  id="pest-species"
                  value={pest}
                  onChange={(e) => setPest(e.target.value)}
                  className="modern-select"
                >
                  {(PEST_MAPPING[crop] || []).map(p => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="modern-label" htmlFor="pest-district">District (Maharashtra)</label>
                <select
                  id="pest-district"
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="modern-select"
                >
                  {DEFAULT_DISTRICTS.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
                <small style={{ color: '#6B7D72', fontSize: '0.75rem', display: 'block', marginTop: '0.3rem' }}>
                  Ingested real-world meteorological & ERA5 topsoil surveillance
                </small>
              </div>

              <div>
                <label className="modern-label" htmlFor="pest-date">Assessment Date</label>
                <input
                  id="pest-date"
                  type="date"
                  value={assessmentDate}
                  min="2023-06-01"
                  max="2023-10-31"
                  onChange={(e) => setAssessmentDate(e.target.value)}
                  className="modern-input"
                />
                <small style={{ color: '#6B7D72', fontSize: '0.75rem', display: 'block', marginTop: '0.3rem' }}>
                  Available historical window: 2023-06-01 to 2023-10-31
                </small>
              </div>

              <div>
                <label className="modern-label" htmlFor="pest-planting">Crop Sowing / Planting Date</label>
                <input
                  id="pest-planting"
                  type="date"
                  value={plantingDate}
                  onChange={(e) => setPlantingDate(e.target.value)}
                  className="modern-input"
                />
                <small style={{ color: '#6B7D72', fontSize: '0.75rem', display: 'block', marginTop: '0.3rem' }}>
                  Evaluates host tissue vulnerability across growth stages
                </small>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem',
                background: '#FAFBF6',
                border: '1px solid #E2E8D8',
                borderRadius: '8px',
              }}>
                <input
                  id="pest-forecast-toggle"
                  type="checkbox"
                  checked={fetchLiveForecast}
                  onChange={(e) => setFetchLiveForecast(e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: '#10B981', cursor: 'pointer' }}
                />
                <label htmlFor="pest-forecast-toggle" style={{ fontSize: '0.825rem', color: '#1F2937', fontWeight: 600, cursor: 'pointer' }}>
                  Fetch 7-day live numerical forecast (Open-Meteo)
                </label>
              </div>
            </div>

            {error && (
              <div style={{ marginTop: '1.1rem', padding: '0.85rem', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '8px', color: '#B91C1C', fontSize: '0.825rem' }}>
                ⚠️ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary-emerald"
              style={{
                marginTop: '1.35rem',
                width: '100%',
                padding: '0.85rem',
                fontSize: '0.95rem',
              }}
            >
              {loading ? 'Evaluating Biophysical Parameters...' : '🔬 Evaluate Pest Favorability Index →'}
            </button>
          </form>
        </section>

        {/* Assessment Results Display */}
        <section>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Primary Favorability Card */}
              <div className="modern-card" style={{
                border: `2px solid ${getRiskColor(result.risk_category)}`,
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
                padding: '1.5rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.775rem', color: '#6B7D72', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
                      📍 {result.location} · {result.crop.toUpperCase()}
                    </div>
                    <h2 style={{ margin: '0.25rem 0', color: '#111827', fontSize: '1.55rem', fontWeight: 800 }}>
                      {result.pest}
                    </h2>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: '#4B5563', fontStyle: 'italic' }}>
                      {result.scientific_name}
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    {/* Category Badge */}
                    <div style={{
                      background: getRiskColor(result.risk_category),
                      color: '#FFFFFF',
                      fontWeight: 800,
                      padding: '7px 16px',
                      borderRadius: '8px',
                      fontSize: '0.925rem',
                      letterSpacing: '0.04em',
                      boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
                    }}>
                      {result.risk_category} FAVORABILITY
                    </div>

                    {/* Trend Badge */}
                    {(() => {
                      const t = getTrendBadge(result.risk_trend)
                      return (
                        <div style={{
                          background: t.bg,
                          color: t.color,
                          border: `1.5px solid ${t.border}`,
                          fontWeight: 700,
                          padding: '6px 12px',
                          borderRadius: '8px',
                          fontSize: '0.825rem',
                        }}>
                          {t.label}
                        </div>
                      )
                    })()}
                  </div>
                </div>

                {/* Score Meter */}
                <div style={{
                  marginTop: '1.35rem',
                  padding: '1.15rem',
                  background: getRiskBg(result.risk_category),
                  border: `1px solid ${getRiskColor(result.risk_category)}40`,
                  borderRadius: '12px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                    <span style={{ color: '#374151', fontWeight: 600 }}>Environmental Favorability Index (EFI):</span>
                    <strong style={{ color: getRiskColor(result.risk_category), fontSize: '1.3rem', fontWeight: 800 }}>
                      {result.environmental_favorability_score.toFixed(2)} / 1.00
                    </strong>
                  </div>
                  <div style={{ height: '10px', background: '#E5E7EB', borderRadius: '5px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${Math.round(result.environmental_favorability_score * 100)}%`,
                      height: '100%',
                      background: `linear-gradient(90deg, #10B981 0%, ${getRiskColor(result.risk_category)} 100%)`,
                      borderRadius: '5px',
                      transition: 'width 0.6s ease',
                    }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem', fontSize: '0.725rem', color: '#6B7280', fontWeight: 600 }}>
                    <span>0.00 (Inhibiting)</span>
                    <span>0.40 (Conducive)</span>
                    <span>0.70 (Highly Conducive)</span>
                    <span>1.00</span>
                  </div>
                </div>

                {/* Microclimatic Observations Grid */}
                <div style={{ marginTop: '1.35rem' }}>
                  <h4 style={{ margin: '0 0 0.75rem 0', color: '#1F2937', fontSize: '0.95rem', fontWeight: 700 }}>
                    Observed Environmental Conditions ({result.environmental_observations.date})
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem' }}>
                    <div style={{ background: '#FFF7ED', border: '1px solid #FED7AA', padding: '0.85rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.75rem', color: '#9A3412', fontWeight: 600 }}>🌡️ Temperature</span>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#7C2D12', marginTop: '0.15rem' }}>
                        {result.environmental_observations.temperature_mean_c.toFixed(1)}°C
                      </div>
                      <span style={{ fontSize: '0.7rem', color: '#C2410C' }}>
                        7d Avg: {result.environmental_observations.antecedent_mean_temperature_c.toFixed(1)}°C
                      </span>
                    </div>

                    <div style={{ background: '#ECFEFF', border: '1px solid #A5F3FC', padding: '0.85rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.75rem', color: '#0E7490', fontWeight: 600 }}>💧 Humidity</span>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#155E75', marginTop: '0.15rem' }}>
                        {result.environmental_observations.relative_humidity_pct.toFixed(0)}%
                      </div>
                      <span style={{ fontSize: '0.7rem', color: '#0891B2' }}>
                        7d Avg: {result.environmental_observations.antecedent_mean_humidity_pct.toFixed(0)}%
                      </span>
                    </div>

                    <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', padding: '0.85rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.75rem', color: '#1D4ED8', fontWeight: 600 }}>🌧️ Rainfall</span>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1E40AF', marginTop: '0.15rem' }}>
                        {result.environmental_observations.rainfall_mm.toFixed(1)} mm
                      </div>
                      <span style={{ fontSize: '0.7rem', color: '#2563EB' }}>
                        7d Cum: {result.environmental_observations.antecedent_accumulated_rainfall_mm.toFixed(0)} mm
                      </span>
                    </div>

                    <div style={{ background: '#F0FDF4', border: '1px solid #BBF7D0', padding: '0.85rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.75rem', color: '#15803D', fontWeight: 600 }}>🌱 Topsoil Moisture</span>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#166534', marginTop: '0.15rem' }}>
                        {result.environmental_observations.soil_moisture_m3m3 != null
                          ? `${(result.environmental_observations.soil_moisture_m3m3 * 100).toFixed(1)}%`
                          : 'Excluded'}
                      </div>
                      <span style={{ fontSize: '0.7rem', color: '#16A34A' }}>
                        {result.environmental_observations.soil_moisture_m3m3 != null ? 'ERA5-Land 0-7cm' : 'No topsoil sensor'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Contributing Factors */}
                <div style={{ marginTop: '1.35rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
                  <div style={{ background: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: '10px', padding: '1rem' }}>
                    <div style={{ fontSize: '0.825rem', fontWeight: 700, color: '#065F46', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span>✅</span> Conducive Environmental Drivers:
                    </div>
                    {result.contributing_factors.favorable_drivers.length > 0 ? (
                      <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.825rem', color: '#047857', lineHeight: 1.5 }}>
                        {result.contributing_factors.favorable_drivers.map((d, i) => (
                          <li key={i} style={{ marginBottom: '0.3rem' }}>{d}</li>
                        ))}
                      </ul>
                    ) : (
                      <p style={{ margin: 0, fontSize: '0.825rem', color: '#6B7280' }}>None observed under current weather parameters.</p>
                    )}
                  </div>

                  <div style={{ background: '#FFF1F2', border: '1px solid #FECDD3', borderRadius: '10px', padding: '1rem' }}>
                    <div style={{ fontSize: '0.825rem', fontWeight: 700, color: '#9F1239', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span>🛑</span> Limiting / Inhibiting Factors:
                    </div>
                    {result.contributing_factors.limiting_factors.length > 0 ? (
                      <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.825rem', color: '#BE123C', lineHeight: 1.5 }}>
                        {result.contributing_factors.limiting_factors.map((f, i) => (
                          <li key={i} style={{ marginBottom: '0.3rem' }}>{f}</li>
                        ))}
                      </ul>
                    ) : (
                      <p style={{ margin: 0, fontSize: '0.825rem', color: '#6B7280' }}>No severe microclimatic inhibition detected.</p>
                    )}
                  </div>
                </div>

                {/* Actionable Recommendations */}
                <div style={{ marginTop: '1.35rem', background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: '12px', padding: '1.15rem' }}>
                  <h4 style={{ margin: '0 0 0.65rem 0', color: '#92400E', fontSize: '0.925rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>🧑‍🌾</span> Actionable IPM Field Recommendations (ICAR & KVK Protocols)
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '1.35rem', fontSize: '0.85rem', color: '#78350F', lineHeight: 1.6 }}>
                    {result.recommendations.map((rec, i) => (
                      <li key={i} style={{ marginBottom: '0.35rem' }}>{rec}</li>
                    ))}
                  </ul>
                </div>

                {/* 7-Day Forecast Projections (If Available) */}
                {result.forecast_available && result.forecast_summary && (
                  <div style={{ marginTop: '1.35rem', background: '#F8FAFC', borderRadius: '12px', padding: '1.15rem', border: '1px solid #E2E8F0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <h4 style={{ margin: 0, color: '#0F172A', fontSize: '0.925rem', fontWeight: 700 }}>
                        Upcoming 7-Day Numerical Microclimatic Projections ({result.forecast_summary.forecast_days_count} Days)
                      </h4>
                      <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                        Source: {result.forecast_summary.forecast_source}
                      </span>
                    </div>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', fontSize: '0.8rem', borderCollapse: 'collapse', color: '#1E293B' }}>
                        <thead>
                          <tr style={{ borderBottom: '2px solid #CBD5E1', textAlign: 'left', color: '#475569', background: '#F1F5F9' }}>
                            <th style={{ padding: '0.55rem' }}>Date</th>
                            <th style={{ padding: '0.55rem' }}>Temp</th>
                            <th style={{ padding: '0.55rem' }}>RH</th>
                            <th style={{ padding: '0.55rem' }}>Rain</th>
                            <th style={{ padding: '0.55rem' }}>Favorability</th>
                            <th style={{ padding: '0.55rem' }}>Category</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.forecast_summary.daily_projections.map((p, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid #E2E8F0' }}>
                              <td style={{ padding: '0.55rem', fontWeight: 600 }}>{p.date}</td>
                              <td style={{ padding: '0.55rem' }}>{p.temperature_c.toFixed(1)}°C</td>
                              <td style={{ padding: '0.55rem' }}>{p.humidity_pct.toFixed(0)}%</td>
                              <td style={{ padding: '0.55rem' }}>{p.rainfall_mm.toFixed(1)} mm</td>
                              <td style={{ padding: '0.55rem', fontWeight: 700, color: getRiskColor(p.risk_category) }}>
                                {p.favorability_score.toFixed(2)}
                              </td>
                              <td style={{ padding: '0.55rem' }}>
                                <span style={{
                                  background: getRiskColor(p.risk_category),
                                  color: '#FFFFFF',
                                  padding: '3px 8px',
                                  borderRadius: '5px',
                                  fontSize: '0.725rem',
                                  fontWeight: 800,
                                }}>
                                  {p.risk_category}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Biological Limitations & References */}
                <div style={{ marginTop: '1.35rem', paddingTop: '1rem', borderTop: '1px solid #E2E8F0' }}>
                  <details style={{ cursor: 'pointer' }}>
                    <summary style={{ fontSize: '0.825rem', color: '#4B5563', fontWeight: 700 }}>
                      📋 Scientific References, Physiological Thresholds & Grounding Details
                    </summary>
                    <div style={{ marginTop: '0.85rem', fontSize: '0.8rem', color: '#374151' }}>
                      <p style={{ fontWeight: 700, color: '#B45309', marginBottom: '0.35rem' }}>Known Ecological Limitations:</p>
                      <ul style={{ margin: 0, paddingLeft: '1.25rem', lineHeight: 1.5, marginBottom: '0.85rem' }}>
                        {result.limitations.map((lim, i) => (
                          <li key={i} style={{ marginBottom: '0.25rem' }}>{lim}</li>
                        ))}
                      </ul>

                      <p style={{ fontWeight: 700, color: '#1D4ED8', marginBottom: '0.35rem' }}>Scientific Sources & Citations:</p>
                      <ul style={{ margin: 0, paddingLeft: '1.25rem', lineHeight: 1.5 }}>
                        {result.references.map((ref, i) => (
                          <li key={i} style={{ marginBottom: '0.45rem' }}>
                            <strong>{ref.title}</strong> — {ref.authors} ({ref.year}). <em>{ref.institution_or_journal}</em>.{' '}
                            {ref.url && (
                              <a href={ref.url} target="_blank" rel="noopener noreferrer" style={{ color: '#059669', textDecoration: 'underline', fontWeight: 600 }}>
                                [Official ICAR Bulletin]
                              </a>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </details>
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
              <span style={{ fontSize: '3rem', display: 'block', marginBottom: '0.85rem' }}>🐛</span>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#13241B', fontSize: '1.35rem', fontWeight: 800 }}>
                Awaiting Biophysical Screening Request
              </h3>
              <p style={{ margin: 0, fontSize: '0.925rem', maxWidth: '460px', marginInline: 'auto', lineHeight: 1.6 }}>
                Select your crop, target pest, and district from the left panel and click <strong>Evaluate Pest Favorability</strong> to assess ambient temperature, humidity, rainfall, and ERA5 topsoil favorability.
              </p>
            </div>
          )}
        </section>
      </div>
      )}
    </div>
  )
}
