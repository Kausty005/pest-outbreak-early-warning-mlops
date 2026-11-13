import { useState } from 'react'

export default function AuthModal({ onLogin }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('Farm Owner / Agronomist')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Please enter your name.')
      return
    }
    const farmerUser = {
      name: name.trim(),
      email: email.trim() || `${name.trim().toLowerCase().replace(/\s+/g, '')}@agriadapt.ai`,
      role,
      loginTime: new Date().toISOString(),
    }
    localStorage.setItem('agri_auth_user', JSON.stringify(farmerUser))
    onLogin(farmerUser)
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
      padding: '1rem',
    }}>
      <div style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '18px',
        boxShadow: '0 25px 50px -12px rgba(19, 46, 34, 0.25)',
        maxWidth: '460px',
        width: '100%',
        padding: '2.25rem',
        border: '1.5px solid #CBD5BF',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
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
          <h2 style={{ margin: '0 0 0.35rem 0', fontSize: '1.5rem', fontWeight: 800, color: '#13241B', letterSpacing: '-0.02em' }}>
            Sign In to AgriAdapt
          </h2>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#4B5563' }}>
            Enterprise Precision Agricultural Intelligence Platform
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          <div>
            <label className="modern-label" htmlFor="auth-name">Farmer / Operator Name *</label>
            <input
              id="auth-name"
              type="text"
              className="modern-input"
              placeholder="e.g. Kaushal Sharma"
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
              placeholder="e.g. kaushal@farm.org"
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
              backgroundColor: '#FFF1F2',
              border: '1px solid #FFE4E6',
              borderRadius: '8px',
              padding: '0.65rem 0.85rem',
              color: '#E11D48',
              fontSize: '0.775rem',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn-primary-emerald"
            style={{ width: '100%', marginTop: '0.5rem', padding: '0.75rem' }}
          >
            Enter Precision Dashboard →
          </button>
        </form>

        <div style={{
          marginTop: '1.25rem',
          textAlign: 'center',
          fontSize: '0.725rem',
          color: '#94A3B8',
          borderTop: '1px solid #F1F5F9',
          paddingTop: '0.9rem',
        }}>
          Persistent Local Session · Automated Profile Recovery
        </div>
      </div>
    </div>
  )
}

