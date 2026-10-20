import { useState, useEffect } from 'react'
import { fertilizerApi } from '../services/api'

const VALID_CROPS = [
  'Rice',
  'Wheat',
  'Sugarcane',
  'Kharif Maize',
  'Rabi Maize',
  'Kharif Rice',
  'Rice-Rabi',
]

const STATES = [
  'Maharashtra',
  'Andhra Pradesh',
  'Bihar',
  'Gujarat',
  'Haryana',
  'Karnataka',
  'Madhya Pradesh',
  'Punjab',
  'Rajasthan',
  'Tamil Nadu',
  'Telangana',
  'Uttar Pradesh',
  'West Bengal',
]

export default function FertilizerSection({ preselectedCrop }) {
  const [formData, setFormData] = useState({
    crop: 'Rice',
    state_name: 'Maharashtra',
    nitrogen__nutrient_index: '1.45',
    phosphorus__nutrient_index: '2.36',
    potassium__nutrient_index: '1.67',
    soil_ph__nutrient_index: '2.03',
    organic_carbon__nutrient_index: '1.80',
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [modelInfo, setModelInfo] = useState(null)

  useEffect(() => {
    if (preselectedCrop) {
      // Find matching crop from list if possible
      const match = VALID_CROPS.find(c => c.toLowerCase() === preselectedCrop.toLowerCase())
      if (match) {
        setFormData(prev => ({ ...prev, crop: match }))
      }
    }
  }, [preselectedCrop])

  useEffect(() => {
    fertilizerApi.modelInfo().then(setModelInfo).catch(() => {})
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    setError('')
  }

  const loadExample = async () => {
    try {
      setLoading(true)
      const example = await fertilizerApi.example()
      setFormData({
        crop: example.crop || 'Rice',
        state_name: example.state_name || 'Maharashtra',
        nitrogen__nutrient_index: String(example.nitrogen__nutrient_index || '1.34'),
        phosphorus__nutrient_index: String(example.phosphorus__nutrient_index || '1.48'),
        potassium__nutrient_index: String(example.potassium__nutrient_index || '2.52'),
        soil_ph__nutrient_index: String(example.soil_ph__nutrient_index || '2.11'),
        organic_carbon__nutrient_index: String(example.organic_carbon__nutrient_index || '1.75'),
      })
      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = {
        crop: formData.crop,
        state_name: formData.state_name,
        nitrogen__nutrient_index: Number(formData.nitrogen__nutrient_index),
        phosphorus__nutrient_index: Number(formData.phosphorus__nutrient_index),
        potassium__nutrient_index: Number(formData.potassium__nutrient_index),
        soil_ph__nutrient_index: Number(formData.soil_ph__nutrient_index),
        organic_carbon__nutrient_index: Number(formData.organic_carbon__nutrient_index),
      }
      const data = await fertilizerApi.recommend(payload)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fertilizer-container" id="fertilizer">
      <div className="section-header">
        <div>
          <p className="eyebrow">AgriAdapt Nutrient Intelligence</p>
          <h2>District-Calibrated Fertilizer Recommendation</h2>
          <p className="muted">
            Ensemble AI (Random Forest + Extra Trees + GBDT) trained on ICAR-IISS General Fertilizer Recommendations & Soil Health Card Indices.
          </p>
        </div>
        <button type="button" className="secondary-button" onClick={loadExample} disabled={loading}>
          Load Sample Plot (Maharashtra)
        </button>
      </div>

      <div className="content-grid">
        <section className="form-panel">
          <form onSubmit={handleSubmit}>
            <div className="field-grid">
              <div className="form-field">
                <label htmlFor="fert-crop">Target Crop</label>
                <select
                  id="fert-crop"
                  name="crop"
                  value={formData.crop}
                  onChange={handleChange}
                  className="form-select"
                >
                  {VALID_CROPS.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                <small>Select from ICAR-IISS supported crop models</small>
              </div>

              <div className="form-field">
                <label htmlFor="fert-state">State / Territory</label>
                <select
                  id="fert-state"
                  name="state_name"
                  value={formData.state_name}
                  onChange={handleChange}
                  className="form-select"
                >
                  {STATES.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                <small>Agroclimatic zone baseline</small>
              </div>

              <div className="form-field">
                <label htmlFor="fert-n-idx">Nitrogen Nutrient Index (1.0–3.0)</label>
                <input
                  id="fert-n-idx"
                  name="nitrogen__nutrient_index"
                  type="number"
                  step="0.01"
                  min="0.8"
                  max="3.2"
                  value={formData.nitrogen__nutrient_index}
                  onChange={handleChange}
                  required
                />
                <small>1 = Low, 2 = Medium, 3 = High</small>
              </div>

              <div className="form-field">
                <label htmlFor="fert-p-idx">Phosphorus Nutrient Index (1.0–3.0)</label>
                <input
                  id="fert-p-idx"
                  name="phosphorus__nutrient_index"
                  type="number"
                  step="0.01"
                  min="0.8"
                  max="3.2"
                  value={formData.phosphorus__nutrient_index}
                  onChange={handleChange}
                  required
                />
                <small>Phosphate availability index</small>
              </div>

              <div className="form-field">
                <label htmlFor="fert-k-idx">Potassium Nutrient Index (1.0–3.0)</label>
                <input
                  id="fert-k-idx"
                  name="potassium__nutrient_index"
                  type="number"
                  step="0.01"
                  min="0.8"
                  max="3.2"
                  value={formData.potassium__nutrient_index}
                  onChange={handleChange}
                  required
                />
                <small>Potash availability index</small>
              </div>

              <div className="form-field">
                <label htmlFor="fert-ph-idx">Soil pH Nutrient Index (1.0–3.0)</label>
                <input
                  id="fert-ph-idx"
                  name="soil_ph__nutrient_index"
                  type="number"
                  step="0.01"
                  min="0.8"
                  max="3.2"
                  value={formData.soil_ph__nutrient_index}
                  onChange={handleChange}
                  required
                />
                <small>1 = Acidic, 2 = Neutral, 3 = Alkaline</small>
              </div>

              <div className="form-field">
                <label htmlFor="fert-oc-idx">Organic Carbon Index (1.0–3.0)</label>
                <input
                  id="fert-oc-idx"
                  name="organic_carbon__nutrient_index"
                  type="number"
                  step="0.01"
                  min="0.8"
                  max="3.2"
                  value={formData.organic_carbon__nutrient_index}
                  onChange={handleChange}
                  required
                />
                <small>Soil organic matter fertility rating</small>
              </div>
            </div>

            {error && <div className="request-error" role="alert"><p>{error}</p></div>}

            <button type="submit" className="primary-button" disabled={loading}>
              {loading ? 'Computing Dosages...' : 'Calculate Fertilizer Dosages'}
            </button>
          </form>
        </section>

        <aside>
          {result ? (
            <div className="result-card fertilizer-result-card">
              <p className="eyebrow">Optimal Fertilizer Plan</p>
              <h2>{result.crop} · {result.state_name}</h2>
              <p className="muted">Ensemble Model v{result.model_version}</p>

              <div className="nutrient-grid">
                <div className="nutrient-item">
                  <span className="nutrient-label">Nitrogen (N)</span>
                  <span className="nutrient-val">{result.recommendations.nitrogen.value} <small>kg/ha</small></span>
                  <span className="nutrient-chem">{result.recommendations.nitrogen.chemical_form}</span>
                </div>
                <div className="nutrient-item">
                  <span className="nutrient-label">Phosphate (P₂O₅)</span>
                  <span className="nutrient-val">{result.recommendations.phosphorus.value} <small>kg/ha</small></span>
                  <span className="nutrient-chem">{result.recommendations.phosphorus.chemical_form}</span>
                </div>
                <div className="nutrient-item">
                  <span className="nutrient-label">Potash (K₂O)</span>
                  <span className="nutrient-val">{result.recommendations.potassium.value} <small>kg/ha</small></span>
                  <span className="nutrient-chem">{result.recommendations.potassium.chemical_form}</span>
                </div>
              </div>

              <div className="commercial-bags-card">
                <h3>Commercial Fertilizer Bag Equivalents</h3>
                <div className="bags-list">
                  <div className="bag-row">
                    <span>🌾 Urea (46% N)</span>
                    <strong>{result.fertilizer_commercial_equivalent_approx.urea_46_pct_n_kg_ha} kg/ha</strong>
                  </div>
                  <div className="bag-row">
                    <span>🌱 DAP (46% P₂O₅)</span>
                    <strong>{result.fertilizer_commercial_equivalent_approx.dap_46_pct_p2o5_kg_ha} kg/ha</strong>
                  </div>
                  <div className="bag-row">
                    <span>🌿 MOP (60% K₂O)</span>
                    <strong>{result.fertilizer_commercial_equivalent_approx.mop_60_pct_k2o_kg_ha} kg/ha</strong>
                  </div>
                </div>
              </div>

              <div className="advisory-box">
                <p><strong>STCR Field Modulation Rule:</strong> Adjust recommended dosages +/- 25% based on actual laboratory soil tests. Deduct organic manure (FYM) contributions.</p>
              </div>
            </div>
          ) : (
            <div className="empty-result">
              <p>Configure soil nutrient indices and click <strong>Calculate Fertilizer Dosages</strong> to view elemental macronutrients (N, P₂O₅, K₂O) and commercial bag equivalents (Urea, DAP, MOP).</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
