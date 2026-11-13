import { useEffect, useState } from 'react'
import { pestRiskApi } from '../services/api'

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

export default function EnvironmentalPestRiskSection() {
  const [crop, setCrop] = useState('cotton')
  const [pest, setPest] = useState('pink_bollworm')
  const [district, setDistrict] = useState('Nagpur')
  const [assessmentDate, setAssessmentDate] = useState('2023-09-15')
  const [plantingDate, setPlantingDate] = useState('2023-06-15')
  const [fetchLiveForecast, setFetchLiveForecast] = useState(false)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

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
      case 'HIGH': return '#ef4444'
      case 'MODERATE': return '#f59e0b'
      case 'LOW': return '#10b981'
      default: return '#94a3b8'
    }
  }

  const getTrendBadge = (trend) => {
    switch (trend) {
      case 'RISING': return { label: '↗ RISING RISK', color: '#ef4444', bg: 'rgba(239,68,68,0.15)' }
      case 'DECLINING': return { label: '↘ DECLINING RISK', color: '#10b981', bg: 'rgba(16,185,129,0.15)' }
      case 'STABLE': return { label: '→ STABLE', color: '#38bdf8', bg: 'rgba(56,189,248,0.15)' }
      default: return { label: '• HISTORICAL ONLY', color: '#94a3b8', bg: 'rgba(148,163,184,0.15)' }
    }
  }

  return (
    <div className="environmental-pest-risk-container" id="pest-risk-section" style={{ padding: '1rem 0' }}>
      {/* Prominent Experimental Disclaimer Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(15, 23, 42, 0.95) 100%)',
        border: '1px solid #f59e0b',
        borderRadius: '12px',
        padding: '1.2rem 1.5rem',
        marginBottom: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.4rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '1.3rem' }}>🔬</span>
          <strong style={{ color: '#fbbf24', fontSize: '1.05rem', letterSpacing: '0.02em', textTransform: 'uppercase' }}>
            Experimental Environmental Favorability Assessment
          </strong>
          <span style={{
            background: '#f59e0b',
            color: '#0f172a',
            fontSize: '0.72rem',
            fontWeight: 800,
            padding: '2px 8px',
            borderRadius: '4px',
          }}>
            TIER 1 MACRO
          </span>
        </div>
        <p style={{ margin: 0, fontSize: '0.88rem', color: '#e2e8f0', lineHeight: 1.5 }}>
          This assessment evaluates whether environmental conditions are favorable for pest activity.
          It does not predict the probability of an actual pest outbreak and is not a substitute for field surveillance.
        </p>
      </div>

      <div className="content-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 420px) 1fr', gap: '1.5rem' }}>
        {/* Input Parameters Panel */}
        <section className="form-panel" style={{
          background: 'rgba(15, 23, 42, 0.85)',
          padding: '1.5rem',
          borderRadius: '14px',
          border: '1px solid rgba(255,255,255,0.1)',
        }}>
          <div style={{ marginBottom: '1.2rem' }}>
            <p className="eyebrow" style={{ color: '#4ade80', fontSize: '0.75rem', fontWeight: 700, margin: '0 0 0.3rem 0' }}>
              BIOPHYSICAL SCREENING
            </p>
            <h3 style={{ margin: 0, color: '#f8fafc', fontSize: '1.2rem' }}>Configure Assessment</h3>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.2rem 0 0 0' }}>
              Select target crop, pest, and Maharashtra district.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-field">
                <label htmlFor="pest-crop" style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '0.3rem' }}>
                  Target Crop
                </label>
                <select
                  id="pest-crop"
                  value={crop}
                  onChange={handleCropChange}
                  style={{ width: '100%', padding: '0.55rem', borderRadius: '8px', background: '#1e293b', color: '#f8fafc', border: '1px solid #334155' }}
                >
                  {DEFAULT_CROPS.map(c => (
                    <option key={c} value={c}>
                      {c.charAt(0).toUpperCase() + c.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label htmlFor="pest-species" style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '0.3rem' }}>
                  Target Pest Species
                </label>
                <select
                  id="pest-species"
                  value={pest}
                  onChange={(e) => setPest(e.target.value)}
                  style={{ width: '100%', padding: '0.55rem', borderRadius: '8px', background: '#1e293b', color: '#f8fafc', border: '1px solid #334155' }}
                >
                  {(PEST_MAPPING[crop] || []).map(p => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label htmlFor="pest-district" style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '0.3rem' }}>
                  District (Maharashtra)
                </label>
                <select
                  id="pest-district"
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  style={{ width: '100%', padding: '0.55rem', borderRadius: '8px', background: '#1e293b', color: '#f8fafc', border: '1px solid #334155' }}
                >
                  {DEFAULT_DISTRICTS.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
                <small style={{ color: '#64748b', fontSize: '0.72rem' }}>
                  Ingested real-world meteorological & ERA5 topsoil surveillance
                </small>
              </div>

              <div className="form-field">
                <label htmlFor="pest-date" style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '0.3rem' }}>
                  Assessment Date
                </label>
                <input
                  id="pest-date"
                  type="date"
                  value={assessmentDate}
                  min="2023-06-01"
                  max="2023-10-31"
                  onChange={(e) => setAssessmentDate(e.target.value)}
                  style={{ width: '100%', padding: '0.55rem', borderRadius: '8px', background: '#1e293b', color: '#f8fafc', border: '1px solid #334155' }}
                />
                <small style={{ color: '#64748b', fontSize: '0.72rem' }}>
                  Available historical window: 2023-06-01 to 2023-10-31
                </small>
              </div>

              <div className="form-field">
                <label htmlFor="pest-planting" style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '0.3rem' }}>
                  Crop Sowing / Planting Date
                </label>
                <input
                  id="pest-planting"
                  type="date"
                  value={plantingDate}
                  onChange={(e) => setPlantingDate(e.target.value)}
                  style={{ width: '100%', padding: '0.55rem', borderRadius: '8px', background: '#1e293b', color: '#f8fafc', border: '1px solid #334155' }}
                />
                <small style={{ color: '#64748b', fontSize: '0.72rem' }}>
                  Used to evaluate host phenological tissue vulnerability
                </small>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginTop: '0.4rem' }}>
                <input
                  id="pest-forecast-toggle"
                  type="checkbox"
                  checked={fetchLiveForecast}
                  onChange={(e) => setFetchLiveForecast(e.target.checked)}
                  style={{ width: '16px', height: '16px', accentColor: '#10b981' }}
                />
                <label htmlFor="pest-forecast-toggle" style={{ fontSize: '0.82rem', color: '#e2e8f0', cursor: 'pointer' }}>
                  Fetch 7-day live numerical forecast (Open-Meteo)
                </label>
              </div>
            </div>

            {error && (
              <div style={{ marginTop: '1rem', padding: '0.8rem', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid #ef4444', borderRadius: '8px', color: '#fca5a5', fontSize: '0.82rem' }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: '1.2rem',
                width: '100%',
                padding: '0.75rem',
                borderRadius: '8px',
                border: 'none',
                background: loading ? '#475569' : '#10b981',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.9rem',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s',
              }}
            >
              {loading ? 'Evaluating Biophysical Parameters...' : 'Evaluate Pest Favorability'}
            </button>
          </form>
        </section>

        {/* Assessment Results Display */}
        <section>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
              {/* Primary Favorability Card */}
              <div style={{
                background: 'rgba(15, 23, 42, 0.9)',
                borderRadius: '14px',
                padding: '1.5rem',
                border: `1px solid ${getRiskColor(result.risk_category)}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {result.location} · {result.crop.toUpperCase()}
                    </div>
                    <h2 style={{ margin: '0.2rem 0', color: '#f8fafc', fontSize: '1.4rem' }}>
                      {result.pest}
                    </h2>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8', fontStyle: 'italic' }}>
                      {result.scientific_name}
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
                    {/* Category Badge */}
                    <div style={{
                      background: getRiskColor(result.risk_category),
                      color: '#0f172a',
                      fontWeight: 800,
                      padding: '6px 14px',
                      borderRadius: '8px',
                      fontSize: '0.88rem',
                      letterSpacing: '0.04em',
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
                          border: `1px solid ${t.color}`,
                          fontWeight: 700,
                          padding: '5px 10px',
                          borderRadius: '8px',
                          fontSize: '0.78rem',
                        }}>
                          {t.label}
                        </div>
                      )
                    })()}
                  </div>
                </div>

                {/* Score Meter */}
                <div style={{ marginTop: '1.2rem', padding: '1rem', background: 'rgba(30, 41, 59, 0.5)', borderRadius: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
                    <span style={{ color: '#cbd5e1' }}>Environmental Favorability Index (EFI):</span>
                    <strong style={{ color: getRiskColor(result.risk_category), fontSize: '1.1rem' }}>
                      {result.environmental_favorability_score.toFixed(2)} / 1.00
                    </strong>
                  </div>
                  <div style={{ height: '8px', background: '#334155', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${Math.round(result.environmental_favorability_score * 100)}%`,
                      height: '100%',
                      background: getRiskColor(result.risk_category),
                      borderRadius: '4px',
                      transition: 'width 0.5s ease',
                    }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.3rem', fontSize: '0.68rem', color: '#64748b' }}>
                    <span>0.00 (Inhibiting)</span>
                    <span>0.40 (Conducive)</span>
                    <span>0.70 (Highly Conducive)</span>
                    <span>1.00</span>
                  </div>
                </div>

                {/* Microclimatic Observations Grid */}
                <div style={{ marginTop: '1.2rem' }}>
                  <h4 style={{ margin: '0 0 0.6rem 0', color: '#cbd5e1', fontSize: '0.88rem' }}>
                    Observed Environmental Conditions ({result.environmental_observations.date})
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.6rem' }}>
                    <div style={{ background: '#1e293b', padding: '0.6rem', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>🌡️ Temperature</span>
                      <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                        {result.environmental_observations.temperature_mean_c.toFixed(1)}°C
                      </div>
                      <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                        7d Avg: {result.environmental_observations.antecedent_mean_temperature_c.toFixed(1)}°C
                      </span>
                    </div>

                    <div style={{ background: '#1e293b', padding: '0.6rem', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>💧 Humidity</span>
                      <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                        {result.environmental_observations.relative_humidity_pct.toFixed(0)}%
                      </div>
                      <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                        7d Avg: {result.environmental_observations.antecedent_mean_humidity_pct.toFixed(0)}%
                      </span>
                    </div>

                    <div style={{ background: '#1e293b', padding: '0.6rem', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>🌧️ Rainfall</span>
                      <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                        {result.environmental_observations.rainfall_mm.toFixed(1)} mm
                      </div>
                      <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                        7d Cum: {result.environmental_observations.antecedent_accumulated_rainfall_mm.toFixed(0)} mm
                      </span>
                    </div>

                    <div style={{ background: '#1e293b', padding: '0.6rem', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>🌱 Topsoil Moisture</span>
                      <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                        {result.environmental_observations.soil_moisture_m3m3 != null
                          ? `${(result.environmental_observations.soil_moisture_m3m3 * 100).toFixed(1)}%`
                          : 'Unavailable'}
                      </div>
                      <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                        {result.environmental_observations.soil_moisture_m3m3 != null ? 'ERA5-Land 0-7cm' : 'Excluded from index'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Contributing Factors */}
                <div style={{ marginTop: '1.2rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                  <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '10px', padding: '0.8rem' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#34d399', marginBottom: '0.4rem' }}>
                      Conducive Environmental Drivers:
                    </div>
                    {result.contributing_factors.favorable_drivers.length > 0 ? (
                      <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.78rem', color: '#e2e8f0', lineHeight: 1.4 }}>
                        {result.contributing_factors.favorable_drivers.map((d, i) => (
                          <li key={i} style={{ marginBottom: '0.3rem' }}>{d}</li>
                        ))}
                      </ul>
                    ) : (
                      <p style={{ margin: 0, fontSize: '0.78rem', color: '#94a3b8' }}>None observed under current weather.</p>
                    )}
                  </div>

                  <div style={{ background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '10px', padding: '0.8rem' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f87171', marginBottom: '0.4rem' }}>
                      Limiting / Inhibiting Factors:
                    </div>
                    {result.contributing_factors.limiting_factors.length > 0 ? (
                      <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.78rem', color: '#e2e8f0', lineHeight: 1.4 }}>
                        {result.contributing_factors.limiting_factors.map((f, i) => (
                          <li key={i} style={{ marginBottom: '0.3rem' }}>{f}</li>
                        ))}
                      </ul>
                    ) : (
                      <p style={{ margin: 0, fontSize: '0.78rem', color: '#94a3b8' }}>No severe microclimatic inhibition detected.</p>
                    )}
                  </div>
                </div>

                {/* Actionable Recommendations */}
                <div style={{ marginTop: '1.2rem', background: 'rgba(30, 41, 59, 0.7)', borderRadius: '10px', padding: '1rem' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: '#fbbf24', fontSize: '0.88rem' }}>
                    🧑‍🌾 Actionable IPM Field Recommendations
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.8rem', color: '#f1f5f9', lineHeight: 1.5 }}>
                    {result.recommendations.map((rec, i) => (
                      <li key={i} style={{ marginBottom: '0.3rem' }}>{rec}</li>
                    ))}
                  </ul>
                </div>

                {/* 7-Day Forecast Projections (If Available) */}
                {result.forecast_available && result.forecast_summary && (
                  <div style={{ marginTop: '1.2rem', background: '#0f172a', borderRadius: '10px', padding: '1rem', border: '1px solid #334155' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                      <h4 style={{ margin: 0, color: '#38bdf8', fontSize: '0.88rem' }}>
                        Upcoming 7-Day Projections ({result.forecast_summary.forecast_days_count} Days)
                      </h4>
                      <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                        Source: {result.forecast_summary.forecast_source}
                      </span>
                    </div>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', fontSize: '0.75rem', borderCollapse: 'collapse', color: '#cbd5e1' }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left', color: '#94a3b8' }}>
                            <th style={{ padding: '0.4rem' }}>Date</th>
                            <th style={{ padding: '0.4rem' }}>Temp</th>
                            <th style={{ padding: '0.4rem' }}>RH</th>
                            <th style={{ padding: '0.4rem' }}>Rain</th>
                            <th style={{ padding: '0.4rem' }}>Favorability</th>
                            <th style={{ padding: '0.4rem' }}>Category</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.forecast_summary.daily_projections.map((p, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid rgba(51,65,85,0.4)' }}>
                              <td style={{ padding: '0.4rem', fontWeight: 600 }}>{p.date}</td>
                              <td style={{ padding: '0.4rem' }}>{p.temperature_c.toFixed(1)}°C</td>
                              <td style={{ padding: '0.4rem' }}>{p.humidity_pct.toFixed(0)}%</td>
                              <td style={{ padding: '0.4rem' }}>{p.rainfall_mm.toFixed(1)} mm</td>
                              <td style={{ padding: '0.4rem', fontWeight: 700, color: getRiskColor(p.risk_category) }}>
                                {p.favorability_score.toFixed(2)}
                              </td>
                              <td style={{ padding: '0.4rem' }}>
                                <span style={{
                                  background: getRiskColor(p.risk_category),
                                  color: '#0f172a',
                                  padding: '2px 6px',
                                  borderRadius: '4px',
                                  fontSize: '0.68rem',
                                  fontWeight: 700,
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
                <div style={{ marginTop: '1.2rem', paddingTop: '1rem', borderTop: '1px solid #334155' }}>
                  <details style={{ cursor: 'pointer' }}>
                    <summary style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600 }}>
                      📋 Biological Limitations, Scientific Sources & Grounding Details
                    </summary>
                    <div style={{ marginTop: '0.8rem', fontSize: '0.78rem', color: '#cbd5e1' }}>
                      <p style={{ fontWeight: 600, color: '#f59e0b', marginBottom: '0.3rem' }}>Known Limitations:</p>
                      <ul style={{ margin: 0, paddingLeft: '1.2rem', lineHeight: 1.4, marginBottom: '0.8rem' }}>
                        {result.limitations.map((lim, i) => (
                          <li key={i} style={{ marginBottom: '0.2rem' }}>{lim}</li>
                        ))}
                      </ul>

                      <p style={{ fontWeight: 600, color: '#38bdf8', marginBottom: '0.3rem' }}>Scientific Sources & Citations:</p>
                      <ul style={{ margin: 0, paddingLeft: '1.2rem', lineHeight: 1.4 }}>
                        {result.references.map((ref, i) => (
                          <li key={i} style={{ marginBottom: '0.4rem' }}>
                            <strong>{ref.title}</strong> — {ref.authors} ({ref.year}). <em>{ref.institution_or_journal}</em>.{' '}
                            {ref.url && (
                              <a href={ref.url} target="_blank" rel="noopener noreferrer" style={{ color: '#4ade80', textDecoration: 'underline' }}>
                                [Link]
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
            <div style={{
              background: 'rgba(15, 23, 42, 0.6)',
              borderRadius: '14px',
              border: '1px dashed rgba(255,255,255,0.2)',
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#94a3b8',
            }}>
              <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '1rem' }}>🐛</span>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#f8fafc' }}>Awaiting Assessment Request</h3>
              <p style={{ margin: 0, fontSize: '0.88rem', maxWidth: '420px', marginInline: 'auto' }}>
                Select a crop, pest, and district from the left panel and click <strong>Evaluate Pest Favorability</strong> to compute the 7-day biophysical microclimatic suitability index.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

