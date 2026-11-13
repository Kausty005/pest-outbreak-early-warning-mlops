import { useState } from 'react'
import { cropApi, fertilizerApi } from '../services/api'

const CROP_OPTIONS = [
  'Rice', 'Wheat', 'Maize', 'Cotton', 'Sugarcane', 'Soybean', 'Mustard',
  'Banana', 'Tomato', 'Potato', 'Onion', 'Chickpea',
]

const STATE_OPTIONS = [
  'Maharashtra', 'Punjab', 'Uttar Pradesh', 'Madhya Pradesh', 'Rajasthan',
  'Gujarat', 'Haryana', 'Bihar', 'West Bengal', 'Karnataka', 'Andhra Pradesh',
  'Tamil Nadu', 'Telangana',
]

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }

export default function UnifiedInputPanel({ prefill, farmProfile }) {
  const [formData, setFormData] = useState({
    N: prefill?.N ?? 90,
    P: prefill?.P ?? 42,
    K: prefill?.K ?? 43,
    temperature: prefill?.temperature ?? 26.5,
    humidity: prefill?.humidity ?? 78,
    ph: prefill?.ph ?? 6.5,
    rainfall: prefill?.rainfall ?? 180,
    crop: prefill?.crop || farmProfile?.primaryCrop || 'Rice',
    state: prefill?.state || farmProfile?.state || 'Maharashtra',
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [cropResult, setCropResult] = useState(null)
  const [fertResult, setFertResult] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    setError('')
  }

  const handleAutofillSensor = (sensorValues) => {
    if (!sensorValues) return
    setFormData(prev => ({
      ...prev,
      N: sensorValues.N,
      P: sensorValues.P,
      K: sensorValues.K,
      temperature: sensorValues.temperature,
      humidity: sensorValues.humidity,
      ph: sensorValues.ph,
      rainfall: sensorValues.rainfall,
      crop: sensorValues.crop || prev.crop,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const numericPayload = {
      N: Number(formData.N),
      P: Number(formData.P),
      K: Number(formData.K),
      temperature: Number(formData.temperature),
      humidity: Number(formData.humidity),
      ph: Number(formData.ph),
      rainfall: Number(formData.rainfall),
    }

    const fertPayload = {
      crop: formData.crop,
      state_name: formData.state,
      nitrogen__nutrient_index: clamp(Number(formData.N) / 45, 1.0, 3.0),
      phosphorus__nutrient_index: clamp(Number(formData.P) / 30, 1.0, 3.0),
      potassium__nutrient_index: clamp(Number(formData.K) / 40, 1.0, 3.0),
      soil_ph__nutrient_index: clamp(Number(formData.ph) / 3.5, 1.0, 3.0),
      organic_carbon__nutrient_index: 1.8,
    }

    try {
      const [cropRes, fertRes] = await Promise.all([
        cropApi.recommend(numericPayload),
        fertilizerApi.recommend(fertPayload).catch(() => null),
      ])
      setCropResult(cropRes)
      setFertResult(fertRes)
    } catch (err) {
      setError(err.message || 'Error executing AI model inference.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modern-card" style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1.35rem',
      border: '1.5px solid #CBD5BF',
      boxShadow: '0 4px 20px rgba(19, 46, 34, 0.08)',
      padding: '1.75rem',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#059669', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            ⚡ Dual AI Inference Architecture
          </span>
          <h3 style={{ margin: '0.15rem 0 0 0', fontSize: '1.35rem', fontWeight: 800, color: '#13241B', letterSpacing: '-0.02em' }}>
            Unified AI Crop & Nutrient Advisory
          </h3>
          <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: '#4B5563' }}>
            Simultaneous crop suitability prediction & nutrient replenishment sizing in a single synchronized step
          </p>
        </div>

        {prefill && (
          <button
            type="button"
            className="btn-primary-emerald"
            style={{ padding: '0.55rem 1rem', fontSize: '0.825rem' }}
            onClick={() => handleAutofillSensor(prefill)}
          >
            ⚡ Autofill From Selected Sector Probes
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label className="modern-label" htmlFor="rec-crop">Target Standing Crop</label>
            <select
              id="rec-crop"
              name="crop"
              className="modern-select"
              value={formData.crop}
              onChange={handleChange}
            >
              {CROP_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="modern-label" htmlFor="rec-state">Region / Agro-Climatic Zone</label>
            <select
              id="rec-state"
              name="state"
              className="modern-select"
              value={formData.state}
              onChange={handleChange}
            >
              {STATE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        {/* Primary Macro Nutrients */}
        <div style={{
          background: '#FAFBF6',
          border: '1.5px solid #E2E8D8',
          borderRadius: '12px',
          padding: '1.15rem',
        }}>
          <div style={{ fontSize: '0.775rem', fontWeight: 800, color: '#059669', textTransform: 'uppercase', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span>🧪</span> Soil Macronutrient Indices (kg/ha)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <div>
              <label className="modern-label" htmlFor="rec-n">Nitrogen (N)</label>
              <input id="rec-n" type="number" step="any" name="N" value={formData.N} onChange={handleChange} className="modern-input" required />
            </div>
            <div>
              <label className="modern-label" htmlFor="rec-p">Phosphorus (P)</label>
              <input id="rec-p" type="number" step="any" name="P" value={formData.P} onChange={handleChange} className="modern-input" required />
            </div>
            <div>
              <label className="modern-label" htmlFor="rec-k">Potassium (K)</label>
              <input id="rec-k" type="number" step="any" name="K" value={formData.K} onChange={handleChange} className="modern-input" required />
            </div>
          </div>
        </div>

        {/* Environmental & Soil Characteristics */}
        <div style={{
          background: '#FAFBF6',
          border: '1.5px solid #E2E8D8',
          borderRadius: '12px',
          padding: '1.15rem',
        }}>
          <div style={{ fontSize: '0.775rem', fontWeight: 800, color: '#0284C7', textTransform: 'uppercase', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span>🌧️</span> Micro-Climate & Soil Conditions
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            <div>
              <label className="modern-label" htmlFor="rec-temp">Temperature (°C)</label>
              <input id="rec-temp" type="number" step="any" name="temperature" value={formData.temperature} onChange={handleChange} className="modern-input" required />
            </div>
            <div>
              <label className="modern-label" htmlFor="rec-hum">Humidity (%)</label>
              <input id="rec-hum" type="number" step="any" name="humidity" value={formData.humidity} onChange={handleChange} className="modern-input" required />
            </div>
            <div>
              <label className="modern-label" htmlFor="rec-ph">Soil pH</label>
              <input id="rec-ph" type="number" step="any" name="ph" value={formData.ph} onChange={handleChange} className="modern-input" required />
            </div>
            <div>
              <label className="modern-label" htmlFor="rec-rain">Rainfall (mm)</label>
              <input id="rec-rain" type="number" step="any" name="rainfall" value={formData.rainfall} onChange={handleChange} className="modern-input" required />
            </div>
          </div>
        </div>

        {error && (
          <div style={{ backgroundColor: '#FEF2F2', border: '1.5px solid #FCA5A5', borderRadius: '9px', padding: '0.85rem', color: '#B91C1C', fontSize: '0.85rem' }}>
            ⚠️ {error}
          </div>
        )}

        <button
          type="submit"
          className="btn-primary-emerald"
          disabled={loading}
          style={{ padding: '0.85rem 1.4rem', fontSize: '1rem', marginTop: '0.35rem' }}
        >
          {loading ? 'Executing AI Inference Pipeline...' : '⚡ Calculate Optimal Crop & Fertilizer Dosages →'}
        </button>
      </form>

      {/* Model Predictions Output */}
      {cropResult && !loading && (
        <div style={{
          borderTop: '2px solid #E2E8D8',
          paddingTop: '1.35rem',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '1.25rem',
        }}>
          {/* Crop Result Card */}
          <div style={{
            background: 'linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%)',
            border: '2px solid #6EE7B7',
            borderRadius: '14px',
            padding: '1.35rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
            boxShadow: '0 4px 14px rgba(16, 185, 129, 0.15)',
          }}>
            <div style={{ fontSize: '0.775rem', fontWeight: 800, color: '#065F46', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Primary AI Recommended Crop
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#064E3B', textTransform: 'capitalize' }}>
              🌾 {cropResult.predicted_crop}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem', marginTop: '0.35rem' }}>
              {cropResult.top_recommendations?.slice(0, 3).map((r, i) => {
                const pct = Math.round(r.model_score * 100)
                return (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.825rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 700, textTransform: 'capitalize', color: '#065F46' }}>{r.crop}</span>
                      <span style={{ fontWeight: 800, color: '#047857' }}>{pct}% Match</span>
                    </div>
                    <div style={{ background: '#A7F3D0', height: '8px', borderRadius: '999px', overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg, #10B981, #059669)', borderRadius: '999px' }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Fertilizer Dosages */}
          {fertResult && fertResult.recommendations && (
            <div style={{
              background: '#FFFFFF',
              border: '2px solid #CBD5BF',
              borderRadius: '14px',
              padding: '1.35rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.85rem',
              boxShadow: '0 4px 14px rgba(0, 0, 0, 0.05)',
            }}>
              <div style={{ fontSize: '0.775rem', fontWeight: 800, color: '#92400E', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Nutrient Application Plan ({fertResult.crop})
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.65rem' }}>
                <div style={{ background: '#ECFDF5', border: '1.5px solid #A7F3D0', borderRadius: '10px', padding: '0.75rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.725rem', fontWeight: 700, color: '#065F46' }}>N Required</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#047857', marginTop: '0.15rem' }}>
                    {fertResult.recommendations.nitrogen?.value} <span style={{ fontSize: '0.7rem' }}>kg/ha</span>
                  </div>
                </div>
                <div style={{ background: '#FEF3C7', border: '1.5px solid #FDE68A', borderRadius: '10px', padding: '0.75rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.725rem', fontWeight: 700, color: '#92400E' }}>P₂O₅ Required</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#78350F', marginTop: '0.15rem' }}>
                    {fertResult.recommendations.phosphorus?.value} <span style={{ fontSize: '0.7rem' }}>kg/ha</span>
                  </div>
                </div>
                <div style={{ background: '#F3E8FF', border: '1.5px solid #E9D5FF', borderRadius: '10px', padding: '0.75rem', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.725rem', fontWeight: 700, color: '#6B21A8' }}>K₂O Required</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#581C87', marginTop: '0.15rem' }}>
                    {fertResult.recommendations.potassium?.value} <span style={{ fontSize: '0.7rem' }}>kg/ha</span>
                  </div>
                </div>
              </div>

              {fertResult.fertilizer_commercial_equivalent_approx && (
                <div style={{
                  background: '#FAFBF6',
                  border: '1px solid #E2E8D8',
                  borderRadius: '10px',
                  padding: '0.75rem 0.95rem',
                  fontSize: '0.825rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.4rem',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#4B5563' }}>Urea (46% N):</span>
                    <strong style={{ color: '#13241B' }}>{fertResult.fertilizer_commercial_equivalent_approx.urea_46_pct_n_kg_ha} kg/ha</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#4B5563' }}>DAP (46% P₂O₅):</span>
                    <strong style={{ color: '#13241B' }}>{fertResult.fertilizer_commercial_equivalent_approx.dap_46_pct_p2o5_kg_ha} kg/ha</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#4B5563' }}>MOP (60% K₂O):</span>
                    <strong style={{ color: '#13241B' }}>{fertResult.fertilizer_commercial_equivalent_approx.mop_60_pct_k2o_kg_ha} kg/ha</strong>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
