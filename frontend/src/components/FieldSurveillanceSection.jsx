import { useEffect, useState } from 'react'
import { pestSurveillanceApi } from '../services/api'

export default function FieldSurveillanceSection() {
  const [subTab, setSubTab] = useState('dashboard') // 'dashboard' | 'entry' | 'upload' | 'records' | 'schedule'
  const [dashboard, setDashboard] = useState(null)
  const [records, setRecords] = useState([])
  const [readinessGate, setReadinessGate] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  // Single observation form state
  const initialFormState = {
    observation_id: '',
    observation_date: new Date().toISOString().slice(0, 10),
    district: 'Nagpur',
    taluka: 'Hingna',
    village: 'Adegaon',
    latitude: 21.05,
    longitude: 78.95,
    crop: 'cotton',
    crop_variety: 'RCH-659 BG-II',
    pest_common_name: 'Pink Bollworm',
    pest_scientific_name: 'Pectinophora gossypiella',
    pest_incidence_pct: 5.0,
    pest_severity_pct: 3.0,
    trap_type: 'delta_trap',
    trap_catch_count: 4.0,
    plants_sampled: 20,
    plants_affected: 1,
    sampling_method: 'destructive_boll_dissection',
    observation_frequency: 'weekly',
    sowing_date: '2026-06-15',
    crop_growth_stage: 'Boll Development',
    observer_id: 'SCOUT-VIDARBHA-01',
    photo_evidence_sha256: '',
    source_organization: 'AgriAdapt-Maharashtra-Pilot',
    is_draft: false,
  }
  const [formData, setFormData] = useState(initialFormState)
  const [formErrors, setFormErrors] = useState([])
  const [formSubmitting, setFormSubmitting] = useState(false)

  // CSV upload state
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)

  // Review modal state
  const [reviewItem, setReviewItem] = useState(null)
  const [reviewerId, setReviewerId] = useState('KVK-ENTOMOLOGIST-01')
  const [reviewAction, setReviewAction] = useState('APPROVE')
  const [reviewJustification, setReviewJustification] = useState('')
  const [reviewSubmitting, setReviewSubmitting] = useState(false)

  const loadDashboard = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dashRes, recsRes, gateRes] = await Promise.all([
        pestSurveillanceApi.dashboard(),
        pestSurveillanceApi.records({ include_drafts: true }).catch(() => ({ records: [] })),
        pestSurveillanceApi.readinessGate().catch(() => null),
      ])
      setDashboard(dashRes)
      setRecords(recsRes.records || [])
      setReadinessGate(gateRes)
    } catch (err) {
      setError(err.message || 'Failed to load surveillance dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'number' ? (value === '' ? null : Number(value)) : value),
    }))
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormErrors([])
    setSuccessMessage(null)
    setFormSubmitting(true)
    try {
      const res = await pestSurveillanceApi.createRecord(formData)
      setSuccessMessage(`Record ${res.observation_id} saved successfully (${res.validation_status}).`)
      loadDashboard()
      if (!formData.is_draft) {
        setFormData(initialFormState)
      }
    } catch (err) {
      setFormErrors([err.message || 'Failed to submit surveillance record.'])
    } finally {
      setFormSubmitting(false)
    }
  }

  const handleCsvUpload = async (e) => {
    e.preventDefault()
    if (!selectedFile) {
      setError('Please select a CSV file first.')
      return
    }
    setUploading(true)
    setError(null)
    setUploadResult(null)
    try {
      const data = new FormData()
      data.append('file', selectedFile)
      const res = await pestSurveillanceApi.uploadCsv(data)
      setUploadResult(res)
      loadDashboard()
    } catch (err) {
      setError(err.message || 'CSV batch upload failed.')
    } finally {
      setUploading(false)
    }
  }

  const handleReviewSubmit = async (e) => {
    e.preventDefault()
    if (!reviewItem) return
    setReviewSubmitting(true)
    try {
      await pestSurveillanceApi.reviewRecord({
        observation_id: reviewItem.observation_id,
        reviewer_id: reviewerId,
        action: reviewAction,
        justification: reviewJustification || 'Verified against sampling protocol.',
      })
      setReviewItem(null)
      setReviewJustification('')
      loadDashboard()
    } catch (err) {
      alert(`Review failed: ${err.message}`)
    } finally {
      setReviewSubmitting(false)
    }
  }

  return (
    <section className="farm-panel surveillance-section" id="pest-surveillance" aria-label="Field Pest Surveillance">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
        <div>
          <p className="eyebrow">Phase 11 · Ground-Truth Field Surveillance Pipeline</p>
          <h2 style={{ margin: '0.25rem 0' }}>Field Pest Surveillance & Data Acquisition</h2>
          <p style={{ margin: 0, color: '#6b7280', fontSize: '0.9rem' }}>
            Standardized field scouting, pheromone trap logging, batch CSV validation, and human review audit trail.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            className={`btn-action ${subTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setSubTab('dashboard')}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem' }}
          >
            📊 Progress Dashboard
          </button>
          <button
            type="button"
            className={`btn-action ${subTab === 'entry' ? 'active' : ''}`}
            onClick={() => setSubTab('entry')}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem' }}
          >
            📝 Data Entry
          </button>
          <button
            type="button"
            className={`btn-action ${subTab === 'upload' ? 'active' : ''}`}
            onClick={() => setSubTab('upload')}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem' }}
          >
            📤 Batch CSV Upload
          </button>
          <button
            type="button"
            className={`btn-action ${subTab === 'records' ? 'active' : ''}`}
            onClick={() => setSubTab('records')}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem' }}
          >
            📋 Records Queue ({records.length})
          </button>
          <button
            type="button"
            className={`btn-action ${subTab === 'schedule' ? 'active' : ''}`}
            onClick={() => setSubTab('schedule')}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem' }}
          >
            🏛️ Institutional & Schedule
          </button>
        </div>
      </div>

      {/* Critical Invariant Warning Banner */}
      <div
        style={{
          background: '#fffbeb',
          border: '1px solid #fde68a',
          borderLeft: '4px solid #f59e0b',
          borderRadius: '6px',
          padding: '0.75rem 1rem',
          marginBottom: '1.25rem',
          fontSize: '0.85rem',
          color: '#92400e',
        }}
      >
        <strong>⚠️ SCIENTIFIC INVARIANT & ML READINESS GATE:</strong> Supervised 7-day outbreak prediction model training is strictly <strong>BLOCKED</strong>. Current authentic field surveillance records: <strong>{dashboard?.total_records_received || 0}</strong> (Target: &ge;500 multi-season observations). Public agricultural advisories and EFI heuristic scores provide situational intelligence only and are <strong>never converted into training labels</strong>.
      </div>

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', padding: '0.75rem', borderRadius: '6px', color: '#991b1b', marginBottom: '1rem', fontSize: '0.85rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {successMessage && (
        <div style={{ background: '#ecfdf5', border: '1px solid #6ee7b7', padding: '0.75rem', borderRadius: '6px', color: '#065f46', marginBottom: '1rem', fontSize: '0.85rem' }}>
          <strong>Success:</strong> {successMessage}
        </div>
      )}

      {/* ── SUB-TAB 1: DATA ACQUISITION PROGRESS DASHBOARD ── */}
      {subTab === 'dashboard' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827' }}>{dashboard?.total_records_received ?? 0}</div>
              <div style={{ fontSize: '0.8rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.25rem' }}>Authentic Observations</div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.2rem' }}>Target: &ge; 500</div>
            </div>
            <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827' }}>{dashboard?.unique_fields_monitored ?? 0}</div>
              <div style={{ fontSize: '0.8rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.25rem' }}>Monitored Plots</div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.2rem' }}>20 Sentinel Target</div>
            </div>
            <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#10b981' }}>{dashboard?.verified_records_count ?? 0}</div>
              <div style={{ fontSize: '0.8rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.25rem' }}>KVK/Scientist Verified</div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.2rem' }}>Audited entries</div>
            </div>
            <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#ef4444' }}>{dashboard?.positive_outbreak_windows ?? 0}</div>
              <div style={{ fontSize: '0.8rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.25rem' }}>Verified Outbreaks (1)</div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.2rem' }}>&ge; ETL exceedance</div>
            </div>
            <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#3b82f6' }}>{dashboard?.verified_negative_windows ?? 0}</div>
              <div style={{ fontSize: '0.8rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.25rem' }}>Active Negatives (0)</div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.2rem' }}>Verified sub-ETL scouting</div>
            </div>
            <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f59e0b' }}>{dashboard?.unverified_records_count ?? 0}</div>
              <div style={{ fontSize: '0.8rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.25rem' }}>Pending Verification</div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.2rem' }}>Awaiting review</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem' }}>Geographic & Crop Coverage</h4>
              <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', color: '#6b7280' }}>
                Active districts with environmental alignment:
              </p>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
                {['Nagpur', 'Amravati', 'Yavatmal', 'Jalgaon'].map((d) => (
                  <span
                    key={d}
                    style={{
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      background: dashboard?.districts_represented?.includes(d) ? '#d1fae5' : '#f3f4f6',
                      color: dashboard?.districts_represented?.includes(d) ? '#065f46' : '#6b7280',
                      border: '1px solid #e5e7eb',
                    }}
                  >
                    {d} {dashboard?.districts_represented?.includes(d) ? '✓' : '(No data yet)'}
                  </span>
                ))}
              </div>
              <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', color: '#6b7280' }}>
                Target crops: Cotton, Soybean, Maize, Rice.
              </p>
            </div>

            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem' }}>Institutional Access Status</h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#4b5563' }}>
                {dashboard?.institutional_access_status &&
                  Object.entries(dashboard.institutional_access_status).map(([inst, stat]) => (
                    <li key={inst} style={{ marginBottom: '0.35rem' }}>
                      <strong>{inst}:</strong> {stat.split('(')[0]}
                    </li>
                  ))}
              </ul>
            </div>
          </div>

          {/* ── COMPLETE DATA FOUNDATION INVENTORY (PHASE 20) ── */}
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.25rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.75rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.05rem', color: '#111827' }}>📊 Complete Data Foundation Inventory</h3>
                <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: '#6b7280' }}>
                  Audited status of the 5 distinct data streams. Isolated boundaries prevent synthetic or heuristic leakage.
                </p>
              </div>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, padding: '0.25rem 0.6rem', borderRadius: '9999px', background: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd' }}>
                Phase 20 Reconciled
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.9rem' }}>
              {/* Stream 1 */}
              <div style={{ border: '1px solid #e5e7eb', borderRadius: '6px', padding: '0.85rem', background: '#f9fafb' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1f2937' }}>1. Environmental Covariates</span>
                  <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem', borderRadius: '4px', background: '#dcfce7', color: '#15803d', fontWeight: 600 }}>ACQUIRED</span>
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#111827' }}>
                  {readinessGate?.data_foundation_inventory?.environmental_records ?? 612} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#6b7280' }}>records</span>
                </div>
                <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.75rem', color: '#4b5563', lineHeight: '1.3' }}>
                  Open-Meteo & ERA5-Land (4 districts, Jun–Oct 2023). Aligned covariate features.
                </p>
              </div>

              {/* Stream 2 */}
              <div style={{ border: '1px solid #e5e7eb', borderRadius: '6px', padding: '0.85rem', background: '#f9fafb' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1f2937' }}>2. Public Advisories</span>
                  <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem', borderRadius: '4px', background: '#dbeafe', color: '#1d4ed8', fontWeight: 600 }}>ACQUIRED</span>
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#111827' }}>
                  {readinessGate?.data_foundation_inventory?.public_advisories ?? 49} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#6b7280' }}>bulletins</span>
                </div>
                <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.75rem', color: '#4b5563', lineHeight: '1.3' }}>
                  SAU & KVK advisories. Qualitative intelligence only — strictly isolated from ML labels.
                </p>
              </div>

              {/* Stream 3 */}
              <div style={{ border: '1px solid #e5e7eb', borderRadius: '6px', padding: '0.85rem', background: '#f9fafb' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1f2937' }}>3. Historical Research Trials</span>
                  <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem', borderRadius: '4px', background: '#fef3c7', color: '#b45309', fontWeight: 600 }}>QUARANTINED</span>
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#111827' }}>
                  {readinessGate?.data_foundation_inventory?.quarantined_historical_observations ?? 13} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#6b7280' }}>weekly obs</span>
                </div>
                <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.75rem', color: '#4b5563', lineHeight: '1.3' }}>
                  Lande (2005) Akola trial. Double-entry audited (0.00% err). Quarantined from prod.
                </p>
              </div>

              {/* Stream 4 */}
              <div style={{ border: '1px solid #e5e7eb', borderRadius: '6px', padding: '0.85rem', background: '#f9fafb' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1f2937' }}>4. Synthetic Benchmark</span>
                  <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem', borderRadius: '4px', background: '#f3e8ff', color: '#7e22ce', fontWeight: 600 }}>EXPERIMENTAL</span>
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#111827' }}>
                  {(readinessGate?.data_foundation_inventory?.synthetic_benchmark_records ?? 100000).toLocaleString()} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#6b7280' }}>records</span>
                </div>
                <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.75rem', color: '#4b5563', lineHeight: '1.3' }}>
                  Phase 19/20 benchmark pipeline. Seed 42, purged splits. Experimental test only.
                </p>
              </div>

              {/* Stream 5 */}
              <div style={{ border: '1px solid #fecaca', borderRadius: '6px', padding: '0.85rem', background: '#fff5f5' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#991b1b' }}>5. Field Surveillance</span>
                  <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem', borderRadius: '4px', background: '#fee2e2', color: '#b91c1c', fontWeight: 600 }}>STANDBY</span>
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#b91c1c' }}>
                  {readinessGate?.data_foundation_inventory?.authentic_prospective_surveillance_records ?? 0} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#991b1b' }}>observations</span>
                </div>
                <p style={{ margin: '0.35rem 0 0 0', fontSize: '0.75rem', color: '#7f1d1d', lineHeight: '1.3' }}>
                  Authentic commercial scout data. Pilot Kharif 2027 planned. Zero verified labels.
                </p>
              </div>
            </div>
          </div>

          {/* ── PRODUCTION ML TRAINING READINESS GATE (TASK 5 & 6) ── */}
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.25rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.75rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <h3 style={{ margin: 0, fontSize: '1.05rem', color: '#111827' }}>🛑 Production ML Training Readiness Gate</h3>
                  <span
                    style={{
                      padding: '0.2rem 0.65rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      background: readinessGate?.gate_status === 'READY' ? '#dcfce7' : '#fee2e2',
                      color: readinessGate?.gate_status === 'READY' ? '#15803d' : '#b91c1c',
                      border: `1px solid ${readinessGate?.gate_status === 'READY' ? '#bbf7d0' : '#fecaca'}`,
                    }}
                  >
                    STATUS: {readinessGate?.gate_status || 'BLOCKED'}
                  </span>
                </div>
                <p style={{ margin: '0.3rem 0 0 0', fontSize: '0.8rem', color: '#4b5563' }}>
                  Centralized scientific evaluation of 11 agronomic and MLOps criteria. Supervised model training cannot be initiated while blocked.
                </p>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#6b7280', textAlign: 'right' }}>
                Evaluated: {readinessGate?.evaluation_timestamp ? new Date(readinessGate.evaluation_timestamp).toLocaleString() : 'Live'}
              </div>
            </div>

            {/* Blocking reasons callout */}
            {readinessGate?.blocking_reasons && readinessGate.blocking_reasons.length > 0 && (
              <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '6px', padding: '0.85rem 1rem', marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#991b1b', marginBottom: '0.4rem' }}>
                  ⚠️ {readinessGate.blocking_reasons.length} Scientific & Data Gates Blocking Production Training:
                </div>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.78rem', color: '#7f1d1d' }}>
                  {readinessGate.blocking_reasons.map((reason, idx) => (
                    <li key={idx} style={{ marginBottom: '0.25rem' }}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Criteria Checklist Table */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                <thead>
                  <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb', textAlign: 'left' }}>
                    <th style={{ padding: '0.6rem 0.75rem', color: '#4b5563', fontWeight: 600 }}>Criterion</th>
                    <th style={{ padding: '0.6rem 0.75rem', color: '#4b5563', fontWeight: 600 }}>Target Requirement</th>
                    <th style={{ padding: '0.6rem 0.75rem', color: '#4b5563', fontWeight: 600 }}>Current Project State</th>
                    <th style={{ padding: '0.6rem 0.75rem', color: '#4b5563', fontWeight: 600 }}>Gate Status</th>
                  </tr>
                </thead>
                <tbody>
                  {readinessGate?.criteria ? (
                    readinessGate.criteria.map((c, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600, color: '#1f2937' }}>{c.name}</td>
                        <td style={{ padding: '0.6rem 0.75rem', color: '#4b5563' }}>{c.target_requirement}</td>
                        <td style={{ padding: '0.6rem 0.75rem', color: '#4b5563', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {typeof c.actual_state === 'object' ? JSON.stringify(c.actual_state) : String(c.actual_state)}
                        </td>
                        <td style={{ padding: '0.6rem 0.75rem' }}>
                          <span
                            style={{
                              padding: '0.15rem 0.45rem',
                              borderRadius: '4px',
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              background: c.is_satisfied ? '#dcfce7' : '#fee2e2',
                              color: c.is_satisfied ? '#15803d' : '#b91c1c',
                            }}
                          >
                            {c.is_satisfied ? '✓ SATISFIED' : '✕ BLOCKED'}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" style={{ padding: '1rem', textAlign: 'center', color: '#9ca3af' }}>
                        Loading readiness gate criteria...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── SUB-TAB 2: SINGLE FIELD OBSERVATION DATA ENTRY ── */}
      {subTab === 'entry' && (
        <form onSubmit={handleFormSubmit} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.05rem' }}>Direct Field Observation Entry Form</h3>
          <p style={{ margin: '0 0 1rem 0', color: '#6b7280', fontSize: '0.85rem' }}>
            Enter verified physical scouting or pheromone trap data. Unchecked observations enter the review queue as UNVERIFIED.
          </p>

          {formErrors.length > 0 && (
            <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', padding: '0.75rem', borderRadius: '6px', color: '#991b1b', marginBottom: '1rem', fontSize: '0.85rem' }}>
              {formErrors.map((err, i) => (
                <div key={i}>⚠️ {err}</div>
              ))}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Observation ID (Optional)</label>
              <input
                type="text"
                name="observation_id"
                value={formData.observation_id}
                onChange={handleFormChange}
                placeholder="Auto-generated if blank"
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Observation Date *</label>
              <input
                type="date"
                name="observation_date"
                value={formData.observation_date}
                onChange={handleFormChange}
                required
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>District *</label>
              <select
                name="district"
                value={formData.district}
                onChange={handleFormChange}
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
              >
                <option value="Nagpur">Nagpur</option>
                <option value="Amravati">Amravati</option>
                <option value="Yavatmal">Yavatmal</option>
                <option value="Jalgaon">Jalgaon</option>
                <option value="Akola">Akola</option>
                <option value="Wardha">Wardha</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Taluka & Village</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  name="taluka"
                  value={formData.taluka}
                  onChange={handleFormChange}
                  placeholder="Taluka"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
                <input
                  type="text"
                  name="village"
                  value={formData.village}
                  onChange={handleFormChange}
                  placeholder="Village"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>GPS Coordinates (Lat, Lon)</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="number"
                  step="0.0001"
                  name="latitude"
                  value={formData.latitude}
                  onChange={handleFormChange}
                  placeholder="Lat (15.6 - 22.1)"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
                <input
                  type="number"
                  step="0.0001"
                  name="longitude"
                  value={formData.longitude}
                  onChange={handleFormChange}
                  placeholder="Lon (72.6 - 80.9)"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Crop & Variety *</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <select
                  name="crop"
                  value={formData.crop}
                  onChange={handleFormChange}
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                >
                  <option value="cotton">Cotton</option>
                  <option value="soybean">Soybean</option>
                  <option value="maize">Maize</option>
                  <option value="rice">Rice</option>
                </select>
                <input
                  type="text"
                  name="crop_variety"
                  value={formData.crop_variety}
                  onChange={handleFormChange}
                  placeholder="e.g. BG-II"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Target Pest *</label>
              <select
                name="pest_common_name"
                value={formData.pest_common_name}
                onChange={handleFormChange}
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
              >
                {formData.crop === 'cotton' && (
                  <>
                    <option value="Pink Bollworm">Pink Bollworm</option>
                    <option value="American Bollworm">American Bollworm</option>
                    <option value="Spotted Bollworm">Spotted Bollworm</option>
                    <option value="Whitefly">Whitefly</option>
                    <option value="Aphids">Aphids</option>
                    <option value="Jassids">Jassids</option>
                  </>
                )}
                {formData.crop === 'soybean' && (
                  <>
                    <option value="Tobacco Caterpillar">Tobacco Caterpillar</option>
                    <option value="Girdle Beetle">Girdle Beetle</option>
                    <option value="Semilooper">Semilooper</option>
                  </>
                )}
                {formData.crop === 'maize' && (
                  <>
                    <option value="Fall Armyworm">Fall Armyworm</option>
                    <option value="Stem Borer">Stem Borer</option>
                  </>
                )}
                {formData.crop === 'rice' && (
                  <>
                    <option value="Brown Planthopper">Brown Planthopper</option>
                    <option value="Yellow Stem Borer">Yellow Stem Borer</option>
                    <option value="Leaf Folder">Leaf Folder</option>
                  </>
                )}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Sampling Method</label>
              <select
                name="sampling_method"
                value={formData.sampling_method}
                onChange={handleFormChange}
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
              >
                <option value="destructive_boll_dissection">Destructive Boll Dissection (20 bolls)</option>
                <option value="fixed_plot_scouting">Fixed Plot Scouting (W-path)</option>
                <option value="pheromone_trap_monitoring">Pheromone Trap Monitoring</option>
                <option value="roving_survey">Roving Survey</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Plants Sampled & Affected</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="number"
                  name="plants_sampled"
                  value={formData.plants_sampled ?? ''}
                  onChange={handleFormChange}
                  placeholder="Sampled (e.g. 20)"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
                <input
                  type="number"
                  name="plants_affected"
                  value={formData.plants_affected ?? ''}
                  onChange={handleFormChange}
                  placeholder="Affected (e.g. 2)"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Incidence (%) & Severity (%)</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="number"
                  step="0.1"
                  name="pest_incidence_pct"
                  value={formData.pest_incidence_pct ?? ''}
                  onChange={handleFormChange}
                  placeholder="Incidence %"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
                <input
                  type="number"
                  step="0.1"
                  name="pest_severity_pct"
                  value={formData.pest_severity_pct ?? ''}
                  onChange={handleFormChange}
                  placeholder="Severity %"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Trap Type & Moths/Night</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  name="trap_type"
                  value={formData.trap_type ?? ''}
                  onChange={handleFormChange}
                  placeholder="Trap type"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
                <input
                  type="number"
                  step="0.1"
                  name="trap_catch_count"
                  value={formData.trap_catch_count ?? ''}
                  onChange={handleFormChange}
                  placeholder="Moths/night"
                  style={{ width: '50%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Observer ID *</label>
              <input
                type="text"
                name="observer_id"
                value={formData.observer_id}
                onChange={handleFormChange}
                placeholder="SCOUT-XXX-01"
                required
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: '#4b5563', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="is_draft"
                checked={formData.is_draft}
                onChange={handleFormChange}
              />
              Save as Incomplete Draft (bypasses mandatory field constraints)
            </label>
            <button
              type="submit"
              disabled={formSubmitting}
              className="btn-action active"
              style={{ padding: '0.55rem 1.25rem', fontSize: '0.875rem' }}
            >
              {formSubmitting ? 'Validating...' : (formData.is_draft ? '💾 Save Draft' : '📤 Submit for Verification')}
            </button>
          </div>
        </form>
      )}

      {/* ── SUB-TAB 3: BATCH CSV UPLOAD & QUALITY VALIDATION ── */}
      {subTab === 'upload' && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.05rem' }}>Batch CSV Ingestion & Structural Quality Review</h3>
          <p style={{ margin: '0 0 1rem 0', color: '#6b7280', fontSize: '0.85rem' }}>
            Upload genuine field surveillance CSV files (e.g. from KVK trials or university scouting). Raw data is cryptographically hashed with SHA-256 and isolated.
          </p>

          <form onSubmit={handleCsvUpload} style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              style={{ fontSize: '0.85rem' }}
            />
            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="btn-action active"
              style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }}
            >
              {uploading ? 'Validating CSV...' : '🔍 Validate & Ingest CSV'}
            </button>
          </form>

          {uploadResult && (
            <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1rem' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem' }}>Batch Validation Results: {uploadResult.filename}</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ background: '#fff', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e5e7eb', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{uploadResult.total_rows_processed}</div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Total Rows</div>
                </div>
                <div style={{ background: '#fff', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e5e7eb', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#10b981' }}>{uploadResult.valid_rows_count}</div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Valid Rows</div>
                </div>
                <div style={{ background: '#fff', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e5e7eb', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ef4444' }}>{uploadResult.invalid_rows_count}</div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Invalid Rows</div>
                </div>
                <div style={{ background: '#fff', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e5e7eb', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f59e0b' }}>{uploadResult.duplicates_detected}</div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Duplicates</div>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#6b7280', fontFamily: 'monospace' }}>
                SHA-256: {uploadResult.file_sha256}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── SUB-TAB 4: RECORDS & REVIEW QUEUE ── */}
      {subTab === 'records' && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.05rem' }}>Recorded Surveillance Observations ({records.length})</h3>
          <p style={{ margin: '0 0 1rem 0', color: '#6b7280', fontSize: '0.85rem' }}>
            Ground-truth records stored in local processing queue. Click &quot;Review&quot; to inspect notes, audit changes, or approve records.
          </p>

          {records.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#9ca3af', fontSize: '0.9rem' }}>
              No field surveillance records recorded yet. Use the Data Entry form or CSV Batch Upload to ingest authentic observations.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb', textAlign: 'left' }}>
                    <th style={{ padding: '0.5rem' }}>ID</th>
                    <th style={{ padding: '0.5rem' }}>Date</th>
                    <th style={{ padding: '0.5rem' }}>District</th>
                    <th style={{ padding: '0.5rem' }}>Crop / Variety</th>
                    <th style={{ padding: '0.5rem' }}>Pest</th>
                    <th style={{ padding: '0.5rem' }}>Incidence</th>
                    <th style={{ padding: '0.5rem' }}>Trap Catch</th>
                    <th style={{ padding: '0.5rem' }}>Status</th>
                    <th style={{ padding: '0.5rem' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((r) => (
                    <tr key={r.observation_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '0.5rem', fontFamily: 'monospace', fontSize: '0.75rem' }}>{r.observation_id}</td>
                      <td style={{ padding: '0.5rem' }}>{r.observation_date}</td>
                      <td style={{ padding: '0.5rem' }}>{r.district}</td>
                      <td style={{ padding: '0.5rem' }}>{r.crop} {r.crop_variety ? `(${r.crop_variety})` : ''}</td>
                      <td style={{ padding: '0.5rem' }}>{r.pest_common_name}</td>
                      <td style={{ padding: '0.5rem' }}>{r.pest_incidence_pct != null ? `${r.pest_incidence_pct}%` : '—'}</td>
                      <td style={{ padding: '0.5rem' }}>{r.trap_catch_count != null ? r.trap_catch_count : '—'}</td>
                      <td style={{ padding: '0.5rem' }}>
                        <span
                          style={{
                            padding: '0.2rem 0.45rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            background:
                              r.verification_status?.includes('VERIFIED') || r.verification_status?.includes('VALIDATED')
                                ? '#d1fae5'
                                : r.verification_status === 'DRAFT'
                                ? '#fef3c7'
                                : '#fee2e2',
                            color:
                              r.verification_status?.includes('VERIFIED') || r.verification_status?.includes('VALIDATED')
                                ? '#065f46'
                                : r.verification_status === 'DRAFT'
                                ? '#92400e'
                                : '#991b1b',
                          }}
                        >
                          {r.verification_status || 'UNVERIFIED'}
                        </span>
                      </td>
                      <td style={{ padding: '0.5rem' }}>
                        <button
                          type="button"
                          className="btn-action"
                          onClick={() => setReviewItem(r)}
                          style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── SUB-TAB 5: INSTITUTIONAL SCHEDULE & COLLABORATION ── */}
      {subTab === 'schedule' && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.05rem' }}>Prospective Kharif 2027 Field Pilot & Institutional Packages</h3>
          <p style={{ margin: '0 0 1rem 0', color: '#6b7280', fontSize: '0.85rem' }}>
            Timeline and formal collaboration request documents prepared for Maharashtra agricultural institutions.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ background: '#f9fafb', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem' }}>📅 Kharif 2027 Timeline</h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#4b5563', lineHeight: 1.6 }}>
                <li><strong>Dec 2026 – Feb 2027:</strong> Finalize student/supervisor credentials & dispatch requests.</li>
                <li><strong>Mar 2027 – May 2027:</strong> Execute KVK On-Farm Trial data sharing agreements.</li>
                <li><strong>June 15, 2027:</strong> Sowing window begins; activate 20 sentinel plots.</li>
                <li><strong>July 1 – Oct 31, 2027:</strong> 16 weekly longitudinal scouting visits (320 observations).</li>
                <li><strong>Nov 2027:</strong> Quality review, spatial-temporal alignment, and ML readiness evaluation.</li>
              </ul>
            </div>

            <div style={{ background: '#f9fafb', padding: '1rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem' }}>📁 Institutional Request Packages</h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#4b5563', lineHeight: 1.6 }}>
                <li><code>docs/institutional_data_request_cropsap.md</code> (Statewide CROPSAP)</li>
                <li><code>docs/institutional_data_request_icar_cicr.md</code> (ICAR-CICR Nagpur)</li>
                <li><code>docs/institutional_data_request_kvk_nagpur.md</code> (KVK Nagpur)</li>
                <li><code>docs/institutional_data_request_kvk_yavatmal.md</code> (KVK Yavatmal)</li>
                <li><code>docs/institutional_data_request_pdkv_akola.md</code> (Dr. PDKV Akola)</li>
                <li><code>docs/institutional_data_request_vnmkv_parbhani.md</code> (VNMKV Parbhani)</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* ── HUMAN REVIEW MODAL ── */}
      {reviewItem && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#fff', borderRadius: '8px', padding: '1.5rem', width: '90%', maxWidth: '500px' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Review Observation: {reviewItem.observation_id}</h3>
            <p style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', color: '#6b7280' }}>
              {reviewItem.crop} · {reviewItem.pest_common_name} · {reviewItem.district} ({reviewItem.observation_date})
            </p>

            <form onSubmit={handleReviewSubmit}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Reviewer Identifier</label>
                <input
                  type="text"
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  required
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Action</label>
                <select
                  value={reviewAction}
                  onChange={(e) => setReviewAction(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                >
                  <option value="APPROVE">Approve (Promote to KVK_EXPERT_VALIDATED)</option>
                  <option value="REJECT">Reject (Flag as Invalid / Low Quality)</option>
                </select>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' }}>Audit Justification *</label>
                <textarea
                  rows={3}
                  value={reviewJustification}
                  onChange={(e) => setReviewJustification(e.target.value)}
                  placeholder="State basis of validation (e.g. verified boll dissection photos and scout log)."
                  required
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '6px', fontSize: '0.85rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button
                  type="button"
                  className="btn-action"
                  onClick={() => setReviewItem(null)}
                  style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reviewSubmitting}
                  className="btn-action active"
                  style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }}
                >
                  {reviewSubmitting ? 'Recording...' : 'Submit Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}

