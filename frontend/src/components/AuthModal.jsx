import { useState } from 'react'
import { PRESET_FARMERS, ensurePresetFarmsInitialized, sanitizeUserId } from '../utils/userFarmStorage'

export default function AuthModal({ onLogin, onCancel }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('Farm Owner / Agronomist')
  const [error, setError] = useState('')

  const handleSelectPreset = (farmer) => {
    ensurePresetFarmsInitialized()
    const userObj = {
      id: sanitizeUserId(farmer),
      name: farmer.name,
      email: `${sanitizeUserId(farmer)}@agriadapt.ai`,
      role: farmer.role,
      state: farmer.state,
      district: farmer.district,
      loginTime: new Date().toISOString(),
    }
    localStorage.setItem('agri_auth_user', JSON.stringify(userObj))
    onLogin(userObj)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Please enter your name.')
      return
    }
    const userObj = {
      id: sanitizeUserId({ name: name.trim() }),
      name: name.trim(),
      email: email.trim() || `${name.trim().toLowerCase().replace(/\s+/g, '')}@agriadapt.ai`,
      role,
      loginTime: new Date().toISOString(),
    }
    localStorage.setItem('agri_auth_user', JSON.stringify(userObj))
    onLogin(userObj)
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.65)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '1.25rem',
      overflowY: 'auto',
    }}>
      <div style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '20px',
        boxShadow: '0 25px 50px -12px rgba(19, 46, 34, 0.25)',
        maxWidth: '520px',
        width: '100%',
        padding: '2.25rem',
        border: '1.5px solid #CBD5BF',
        position: 'relative',
      }}>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            style={{
              position: 'absolute',
              top: '1.25rem',
              right: '1.25rem',
              background: '#F3F4F6',
              border: 'none',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              fontSize: '1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#4B5563',
            }}
            title="Close"
          >
            ✕
          </button>
        )}

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{
            width: '52px',
            height: '52px',
            background: 'linear-gradient(135deg, #10B981 0%, #047857 100%)',
            boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
            borderRadius: '14px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.75rem',
            marginBottom: '0.85rem',
          }}>
            🌿
          </div>
          <h2 style={{ margin: '0 0 0.35rem 0', fontSize: '1.55rem', fontWeight: 800, color: '#13241B', letterSpacing: '-0.02em' }}>
            Sign In to AgriAdapt
          </h2>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#4B5563' }}>
            Multi-Tenant Precision Agricultural Intelligence Platform
          </p>
        </div>

        {/* Quick-Switch Preset Farmers */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{
            fontSize: '0.75rem',
            fontWeight: 800,
            color: '#059669',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            marginBottom: '0.65rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}>
            <span>⚡</span> One-Click Farmer Estate Profiles
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.6rem' }}>
            {PRESET_FARMERS.map(f => (
              <div
                key={f.id}
                onClick={() => handleSelectPreset(f)}
                style={{
                  background: '#FAFBF6',
                  border: '1.5px solid #CBD5BF',
                  borderRadius: '12px',
                  padding: '0.75rem 1rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#10B981'
                  e.currentTarget.style.background = '#ECFDF5'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#CBD5BF'
                  e.currentTarget.style.background = '#FAFBF6'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    background: f.badgeColor,
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.1rem',
                  }}>
                    {f.avatar}
                  </div>
                  <div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#13241B' }}>
                      {f.name}
                    </div>
                    <div style={{ fontSize: '0.725rem', color: '#4B5563' }}>
                      {f.state} · {f.primaryCrop} Estate ({f.initialFarm.area} Ac, {f.initialFarm.zones.length} Sectors)
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleSelectPreset(f)
                  }}
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    color: '#059669',
                    background: '#D1FAE5',
                    border: '1px solid #A7F3D0',
                    padding: '6px 12px',
                    borderRadius: '7px',
                    cursor: 'pointer',
                  }}
                >
                  Load Estate →
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          margin: '1.25rem 0',
        }}>
          <div style={{ flex: 1, height: '1px', background: '#E2E8D8' }} />
          <span style={{ fontSize: '0.75rem', color: '#6B7D72', fontWeight: 600 }}>OR SIGN IN AS CUSTOM FARMER</span>
          <div style={{ flex: 1, height: '1px', background: '#E2E8D8' }} />
        </div>

        {/* Custom Farmer Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label className="modern-label" htmlFor="auth-name">Farmer / Operator Name *</label>
            <input
              id="auth-name"
              type="text"
              className="modern-input"
              placeholder="e.g. Vikram Verma"
              value={name}
              onChange={(e) => { setName(e.target.value); setError('') }}
              required
            />
          </div>

          <div>
            <label className="modern-label" htmlFor="auth-email">Contact Email (Optional)</label>
            <input
              id="auth-email"
              type="email"
              className="modern-input"
              placeholder="e.g. vikram@myfarm.org"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="modern-label" htmlFor="auth-role">Role & Access Tier</label>
            <select
              id="auth-role"
              className="modern-select"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="Farm Owner / Agronomist">Farm Owner / Agronomist</option>
              <option value="Field Operations Manager">Field Operations Manager</option>
              <option value="Entomologist / Researcher">Entomologist / Researcher</option>
              <option value="Systems Engineer">Systems Engineer</option>
            </select>
          </div>

          {error && (
            <div style={{
              backgroundColor: '#FEF2F2',
              border: '1.5px solid #FCA5A5',
              borderRadius: '8px',
              padding: '0.65rem 0.85rem',
              color: '#B91C1C',
              fontSize: '0.775rem',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn-primary-emerald"
            style={{ width: '100%', marginTop: '0.35rem', padding: '0.85rem' }}
          >
            Enter Precision Dashboard →
          </button>
        </form>

        <div style={{
          marginTop: '1.25rem',
          textAlign: 'center',
          fontSize: '0.725rem',
          color: '#6B7D72',
          borderTop: '1px solid #E2E8D8',
          paddingTop: '0.85rem',
        }}>
          Independent Multi-User Estates · Isolated Telemetry & Crop Lifecycles
        </div>
      </div>
    </div>
  )
}
