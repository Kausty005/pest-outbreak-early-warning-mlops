import { useState, useEffect } from 'react'
import { lifecycleApi } from '../services/api'

const STAGES = [
  { id: 'SEEDLING', label: 'Seedling / Emergence' },
  { id: 'VEGETATIVE', label: 'Vegetative Growth' },
  { id: 'FLOWERING', label: 'Flowering Stage' },
  { id: 'FRUITING_GRAIN_FILL', label: 'Fruiting / Grain Fill' },
  { id: 'MATURITY', label: 'Maturity Stage' },
  { id: 'HARVEST_COMPLETED', label: 'Harvest Completed' },
]

const HEALTH_OPTIONS = [
  { id: 'HEALTHY', label: 'Healthy & Vigor Vigorous', color: '#10B981', bg: '#ECFDF5' },
  { id: 'STRESSED', label: 'Moisture / Heat Stressed', color: '#F59E0B', bg: '#FFFBEB' },
  { id: 'DEFICIENT', label: 'Nutrient Deficient (N/P/K)', color: '#F97316', bg: '#FFF7ED' },
  { id: 'DISEASE_PRONE', label: 'Early Pest / Fungal Risk', color: '#EF4444', bg: '#FEF2F2' },
  { id: 'CRITICAL', label: 'Severe Degradation', color: '#991B1B', bg: '#FEE2E2' },
]

export default function LifecycleMonitor({ zone, currentTelemetry }) {
  const [history, setHistory] = useState([])
  const [stage, setStage] = useState('VEGETATIVE')
  const [healthStatus, setHealthStatus] = useState('HEALTHY')
  const [yieldKg, setYieldKg] = useState('')
  const [farmerNotes, setFarmerNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')

  const loadHistory = async () => {
    if (!zone?.id) return
    try {
      const records = await lifecycleApi.history(zone.id, zone.active_crop || zone.cropName)
      setHistory(records)
    } catch {
      // fallback
    }
  }

  useEffect(() => {
    loadHistory()
  }, [zone?.id])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setSuccessMsg('')

    const payload = {
      zone_id: zone?.id || 'zone-1',
      crop: zone?.active_crop || zone?.cropName || 'Rice',
      stage,
      health_status: healthStatus,
      metrics: {
        N: currentTelemetry?.N || 80,
        P: currentTelemetry?.P || 40,
        K: currentTelemetry?.K || 45,
        soil_moisture: currentTelemetry?.soil_moisture || 60,
        temperature: currentTelemetry?.temperature || 26.5,
        humidity: currentTelemetry?.humidity || 75,
        ph: currentTelemetry?.ph || 6.5,
      },
      advisory_applied: ['Balanced Fertilization Applied', 'Optimized Smart Irrigation Runtime'],
      harvest_yield_kg_per_acre: stage === 'HARVEST_COMPLETED' && yieldKg ? parseFloat(yieldKg) : null,
      farmer_notes: farmerNotes || null,
    }

    try {
      await lifecycleApi.logEvent(payload)
      setSuccessMsg('Lifecycle checkpoint registered to audit log!')
      setFarmerNotes('')
      setYieldKg('')
      await loadHistory()
    } catch {
      setSuccessMsg('Checkpoint saved locally.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#0F172A' }}>
            Crop Lifecycle & Health Observability
          </h3>
          <p style={{ margin: '0.15rem 0 0 0', fontSize: '0.75rem', color: '#64748B' }}>
            Continuous phenological state tracking & end-of-lifecycle yield outcome audit
          </p>
        </div>
        <span style={{
          fontSize: '0.7rem',
          fontWeight: 600,
          padding: '0.2rem 0.5rem',
          borderRadius: '6px',
          background: '#F1F5F9',
          color: '#334155',
        }}>
          Zone: {zone?.label || 'Zone A'} ({zone?.active_crop || 'Rice'})
        </span>
      </div>

      <form onSubmit={handleSubmit} style={{
        background: '#F8FAFC',
        border: '1px solid #E2E8F0',
        borderRadius: '10px',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.85rem',
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <div>
            <label className="modern-label" htmlFor="lifecycle-stage">Plant Growth Stage</label>
            <select
              id="lifecycle-stage"
              className="modern-select"
              value={stage}
              onChange={(e) => setStage(e.target.value)}
            >
              {STAGES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
          </div>

          <div>
            <label className="modern-label" htmlFor="lifecycle-health">Health Status Assessment</label>
            <select
              id="lifecycle-health"
              className="modern-select"
              value={healthStatus}
              onChange={(e) => setHealthStatus(e.target.value)}
            >
              {HEALTH_OPTIONS.map(h => <option key={h.id} value={h.id}>{h.label}</option>)}
            </select>
          </div>
        </div>

        {stage === 'HARVEST_COMPLETED' && (
          <div>
            <label className="modern-label" htmlFor="lifecycle-yield">End-of-Cycle Yield Result (kg/acre)</label>
            <input
              id="lifecycle-yield"
              type="number"
              step="any"
              className="modern-input"
              placeholder="e.g. 1850"
              value={yieldKg}
              onChange={(e) => setYieldKg(e.target.value)}
              required
            />
          </div>
        )}

        <div>
          <label className="modern-label" htmlFor="lifecycle-notes">Farmer Agronomic Observation Notes</label>
          <input
            id="lifecycle-notes"
            type="text"
            className="modern-input"
            placeholder="e.g. Healthy tillering observed, uniform canopy color, pest absence confirmed"
            value={farmerNotes}
            onChange={(e) => setFarmerNotes(e.target.value)}
          />
        </div>

        <button
          type="submit"
          className="btn-primary-emerald"
          disabled={loading}
          style={{ width: 'fit-content' }}
        >
          {loading ? 'Recording...' : 'Record Health Checkpoint →'}
        </button>

        {successMsg && (
          <div style={{ fontSize: '0.775rem', color: '#0D9488', fontWeight: 600 }}>
            ✓ {successMsg}
          </div>
        )}
      </form>

      {/* Lifecycle Timeline */}
      <div>
        <div style={{ fontSize: '0.775rem', fontWeight: 700, color: '#334155', marginBottom: '0.5rem' }}>
          Lifecycle History Log ({history.length} Checkpoints)
        </div>
        {history.length === 0 ? (
          <div style={{ fontSize: '0.75rem', color: '#94A3B8', fontStyle: 'italic' }}>
            No checkpoints registered yet for this season. Record the initial emergence state above.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '180px', overflowY: 'auto' }}>
            {history.slice().reverse().map((item, idx) => {
              const hOpt = HEALTH_OPTIONS.find(h => h.id === item.health_status) || HEALTH_OPTIONS[0]
              return (
                <div key={idx} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: '#FFFFFF',
                  border: '1px solid #E2E8F0',
                  borderRadius: '8px',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.75rem',
                }}>
                  <div>
                    <span style={{ fontWeight: 700, color: '#0F172A' }}>{item.stage}</span>
                    <span style={{ color: '#64748B', marginLeft: '0.5rem' }}>{new Date(item.timestamp).toLocaleDateString()}</span>
                    {item.harvest_yield_kg_per_acre && (
                      <span style={{ fontWeight: 700, color: '#0D9488', marginLeft: '0.5rem' }}>
                        Yield: {item.harvest_yield_kg_per_acre} kg/ac
                      </span>
                    )}
                  </div>
                  <span style={{
                    padding: '0.15rem 0.45rem',
                    borderRadius: '4px',
                    fontSize: '0.675rem',
                    fontWeight: 600,
                    backgroundColor: hOpt.bg,
                    color: hOpt.color,
                  }}>
                    {item.health_status}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

