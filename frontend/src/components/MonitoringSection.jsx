import { useEffect, useState } from 'react'
import { monitoringApi } from '../services/api'

export default function MonitoringSection() {
  const [health, setHealth] = useState(null)
  const [driftSummary, setDriftSummary] = useState(null)
  const [retrainHistory, setRetrainHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState('')
  const [error, setError] = useState('')

  const fetchStatus = async () => {
    setError('')
    try {
      const [h, d, r] = await Promise.all([
        monitoringApi.health().catch(() => null),
        monitoringApi.latestDrift().catch(() => null),
        monitoringApi.retrainHistory(10).catch(() => []),
      ])
      setHealth(h)
      if (d && !d.message) setDriftSummary(d)
      setRetrainHistory(r || [])
    } catch (err) {
      setError(err.message || 'Failed to load monitoring status')
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const handleRunDrift = async () => {
    setLoading(true)
    setActionMessage('')
    setError('')
    try {
      const res = await monitoringApi.runDrift()
      setDriftSummary(res)
      setActionMessage('Drift detection finished successfully.')
      await fetchStatus()
    } catch (err) {
      setError(err.message || 'Failed to execute drift detection')
    } finally {
      setLoading(false)
    }
  }

  const handleTriggerRetrain = async (force = false) => {
    setLoading(true)
    setActionMessage('')
    setError('')
    try {
      const res = await monitoringApi.triggerRetrain(force)
      setActionMessage(res.message || 'Retraining initiated in background.')
      setTimeout(fetchStatus, 3000)
    } catch (err) {
      setError(err.message || 'Failed to trigger retrain')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="form-panel" style={{ maxWidth: '960px', margin: '0 auto 2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <p className="eyebrow">MLOps Lifecycle & Governance</p>
          <h2>Real-Time Model Drift & Retrain Pipeline</h2>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            type="button"
            className="tab-btn"
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
            onClick={fetchStatus}
            disabled={loading}
          >
            🔄 Refresh
          </button>
          <button
            type="button"
            className="tab-btn active"
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
            onClick={handleRunDrift}
            disabled={loading}
          >
            {loading ? 'Running...' : '⚡ Run Drift Check'}
          </button>
          <button
            type="button"
            className="tab-btn"
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', borderColor: 'var(--amber, #f59e0b)' }}
            onClick={() => handleTriggerRetrain(true)}
            disabled={loading}
          >
            🚀 Force Retrain
          </button>
        </div>
      </div>

      {actionMessage && (
        <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: 'rgba(34, 197, 94, 0.1)', border: '1px solid #22c55e', borderRadius: '6px', color: '#22c55e' }}>
          ✓ {actionMessage}
        </div>
      )}

      {error && (
        <div className="request-error" role="alert" style={{ marginTop: '1rem' }}>
          <p>{error}</p>
        </div>
      )}

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', margin: '1.5rem 0' }}>
        <div style={{ background: 'var(--card-bg, #1e293b)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-color, #334155)' }}>
          <p className="eyebrow" style={{ margin: 0 }}>Drift Status</p>
          <h3 style={{ margin: '0.5rem 0', color: driftSummary?.alert ? '#ef4444' : '#22c55e' }}>
            {driftSummary ? (driftSummary.alert ? '⚠️ Drift Alert' : '✅ Stable') : 'No Data'}
          </h3>
          <small style={{ color: 'var(--muted, #94a3b8)' }}>
            Share: {driftSummary ? `${(driftSummary.drift_share * 100).toFixed(0)}%` : 'N/A'}
          </small>
        </div>

        <div style={{ background: 'var(--card-bg, #1e293b)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-color, #334155)' }}>
          <p className="eyebrow" style={{ margin: 0 }}>Drifted Features</p>
          <h3 style={{ margin: '0.5rem 0' }}>
            {driftSummary ? `${driftSummary.drifted_feature_count} / ${driftSummary.features_checked?.length || 7}` : '0 / 7'}
          </h3>
          <small style={{ color: 'var(--muted, #94a3b8)' }}>
            Threshold: ≥ 30% features
          </small>
        </div>

        <div style={{ background: 'var(--card-bg, #1e293b)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-color, #334155)' }}>
          <p className="eyebrow" style={{ margin: 0 }}>Logged Requests</p>
          <h3 style={{ margin: '0.5rem 0' }}>
            {health?.prediction_log?.logged_inputs ?? 0}
          </h3>
          <small style={{ color: 'var(--muted, #94a3b8)' }}>
            Production inputs saved
          </small>
        </div>

        <div style={{ background: 'var(--card-bg, #1e293b)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-color, #334155)' }}>
          <p className="eyebrow" style={{ margin: 0 }}>Last Retrain</p>
          <h3 style={{ margin: '0.5rem 0', fontSize: '1.1rem' }}>
            {health?.retraining?.last_triggered ? new Date(health.retraining.last_triggered).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never'}
          </h3>
          <small style={{ color: 'var(--muted, #94a3b8)' }}>
            Promoted: {health?.retraining?.last_promoted ? 'Yes' : 'No / None'}
          </small>
        </div>
      </div>

      {/* Feature Drift Table */}
      {driftSummary?.feature_drift && (
        <div style={{ marginTop: '1.5rem' }}>
          <h4 style={{ marginBottom: '0.75rem' }}>Feature-Level Drift Breakdown</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '0.5rem' }}>
            {Object.entries(driftSummary.feature_drift).map(([feat, details]) => (
              <div
                key={feat}
                style={{
                  padding: '0.6rem 0.8rem',
                  borderRadius: '6px',
                  background: details.drift_detected ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)',
                  border: `1px solid ${details.drift_detected ? '#ef4444' : '#22c55e'}`,
                  textAlign: 'center',
                }}
              >
                <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{feat}</div>
                <small style={{ color: details.drift_detected ? '#ef4444' : '#22c55e', fontWeight: 600 }}>
                  {details.drift_detected ? 'DRIFT' : 'STABLE'}
                </small>
                {details.p_value !== undefined && (
                  <div style={{ fontSize: '0.7rem', color: 'var(--muted, #94a3b8)' }}>
                    p={details.p_value < 0.001 ? '<0.001' : details.p_value.toFixed(3)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Retrain Events History */}
      {retrainHistory.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h4 style={{ marginBottom: '0.75rem' }}>Recent Retrain Events</h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color, #334155)', textAlign: 'left', color: 'var(--muted, #94a3b8)' }}>
                  <th style={{ padding: '0.5rem' }}>Time</th>
                  <th style={{ padding: '0.5rem' }}>Triggered</th>
                  <th style={{ padding: '0.5rem' }}>Reason</th>
                  <th style={{ padding: '0.5rem' }}>Succeeded</th>
                  <th style={{ padding: '0.5rem' }}>Promoted</th>
                  <th style={{ padding: '0.5rem' }}>Macro F1</th>
                </tr>
              </thead>
              <tbody>
                {retrainHistory.slice().reverse().map((entry, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '0.5rem' }}>{new Date(entry.timestamp).toLocaleTimeString()}</td>
                    <td style={{ padding: '0.5rem' }}>{entry.triggered ? 'Yes' : 'No'}</td>
                    <td style={{ padding: '0.5rem', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{entry.reason}</td>
                    <td style={{ padding: '0.5rem' }}>{entry.retrain_succeeded ? '✅' : entry.triggered ? '❌' : '-'}</td>
                    <td style={{ padding: '0.5rem' }}>{entry.promoted ? '🏆 Yes' : entry.triggered ? 'No' : '-'}</td>
                    <td style={{ padding: '0.5rem' }}>{entry.new_macro_f1 ? (entry.new_macro_f1 * 100).toFixed(2) + '%' : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}
