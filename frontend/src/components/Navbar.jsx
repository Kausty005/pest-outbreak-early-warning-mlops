import { useEffect, useState } from 'react'
import * as api from '../services/api'

export default function Navbar({ activeTab, setActiveTab }) {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    if (api.healthApi && typeof api.healthApi.status === 'function') {
      api.healthApi.status().then(setHealth).catch(() => {})
    }
  }, [])

  return (
    <header className="navbar">
      <a className="brand" href="#home" aria-label="Fieldwise Advisory Home">
        AgriAdapt <span>AI</span>
      </a>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        {health && (
          <div className="status-badge" title={`Crop: ${health.crop_model_version || 'Ready'} | Fertilizer: ${health.fertilizer_model_version || 'Ready'}`}>
            <span className="status-dot"></span>
            <span>{health.status === 'ok' ? 'ML Models Online' : 'Degraded Mode'}</span>
          </div>
        )}

        <nav aria-label="Main navigation">
          <a
            href="#crop-recommendation"
            onClick={(e) => { e.preventDefault(); setActiveTab && setActiveTab('crop'); }}
            style={{ fontWeight: activeTab === 'crop' ? 'bold' : 'normal', color: activeTab === 'crop' ? '#b9e487' : '#e5eee8' }}
          >
            Crop Selection
          </a>
          <a
            href="#fertilizer-advisory"
            onClick={(e) => { e.preventDefault(); setActiveTab && setActiveTab('fertilizer'); }}
            style={{ fontWeight: activeTab === 'fertilizer' ? 'bold' : 'normal', color: activeTab === 'fertilizer' ? '#b9e487' : '#e5eee8' }}
          >
            Fertilizer Intelligence
          </a>
          <a
            href="#unified-advisory"
            onClick={(e) => { e.preventDefault(); setActiveTab && setActiveTab('unified'); }}
            style={{ fontWeight: activeTab === 'unified' ? 'bold' : 'normal', color: activeTab === 'unified' ? '#b9e487' : '#e5eee8' }}
          >
            Unified & Pest Advisory
          </a>
          <a
            href="#monitoring"
            onClick={(e) => { e.preventDefault(); setActiveTab && setActiveTab('monitoring'); }}
            style={{ fontWeight: activeTab === 'monitoring' ? 'bold' : 'normal', color: activeTab === 'monitoring' ? '#b9e487' : '#e5eee8' }}
          >
            MLOps & Drift
          </a>
        </nav>
      </div>
    </header>
  )
}
