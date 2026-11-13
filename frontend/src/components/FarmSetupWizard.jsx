import { useState, useEffect } from 'react'

const CROP_CATALOG = [
  { name: 'Rice', icon: '🌾', duration: '120-140 Days', waterNeed: 'High', soil: 'Clay / Loam' },
  { name: 'Wheat', icon: '🌾', duration: '110-130 Days', waterNeed: 'Medium', soil: 'Loam / Clay' },
  { name: 'Maize', icon: '🌽', duration: '90-110 Days', waterNeed: 'Medium', soil: 'Sandy Loam' },
  { name: 'Cotton', icon: '☁️', duration: '150-180 Days', waterNeed: 'Medium', soil: 'Black Soil' },
  { name: 'Sugarcane', icon: '🎋', duration: '300-365 Days', waterNeed: 'Very High', soil: 'Alluvial' },
  { name: 'Soybean', icon: '🌱', duration: '90-105 Days', waterNeed: 'Medium', soil: 'Red / Black' },
  { name: 'Mustard', icon: '🌼', duration: '100-115 Days', waterNeed: 'Low', soil: 'Sandy Loam' },
  { name: 'Banana', icon: '🍌', duration: '300-360 Days', waterNeed: 'High', soil: 'Alluvial / Loam' },
  { name: 'Tomato', icon: '🍅', duration: '75-90 Days', waterNeed: 'Medium', soil: 'Well-drained Loam' },
  { name: 'Potato', icon: '🥔', duration: '90-110 Days', waterNeed: 'Medium', soil: 'Sandy Loam' },
  { name: 'Onion', icon: '🧅', duration: '120-150 Days', waterNeed: 'Medium', soil: 'Loam' },
  { name: 'Chickpea', icon: '🌿', duration: '95-110 Days', waterNeed: 'Low', soil: 'Clay Loam' },
]

const STATES = [
  'Maharashtra', 'Punjab', 'Uttar Pradesh', 'Madhya Pradesh', 'Rajasthan',
  'Gujarat', 'Haryana', 'Bihar', 'West Bengal', 'Karnataka', 'Andhra Pradesh',
  'Tamil Nadu', 'Telangana', 'Odisha', 'Assam',
]

function rnd(min, max, d = 1) {
  return parseFloat((Math.random() * (max - min) + min).toFixed(d))
}

export function simulateTelemetryForCrop(cropName) {
  const defaults = {
    Rice:      { N: [85, 125], P: [35, 65], K: [40, 85], T: [25, 33], H: [75, 90], pH: [5.8, 6.8], R: [130, 210], M: [65, 85] },
    Wheat:     { N: [75, 115], P: [25, 55], K: [35, 75], T: [16, 24], H: [45, 65], pH: [6.2, 7.5], R: [40, 95], M: [40, 60] },
    Maize:     { N: [80, 135], P: [30, 60], K: [40, 95], T: [22, 31], H: [50, 72], pH: [6.0, 7.0], R: [60, 140], M: [45, 70] },
    Cotton:    { N: [65, 110], P: [25, 50], K: [40, 85], T: [26, 36], H: [45, 68], pH: [6.2, 7.5], R: [35, 95], M: [35, 58] },
    Sugarcane: { N: [110, 150], P: [40, 80], K: [65, 120], T: [24, 35], H: [60, 80], pH: [6.0, 7.5], R: [90, 190], M: [60, 85] },
    Soybean:   { N: [55, 95], P: [30, 65], K: [35, 75], T: [21, 29], H: [55, 75], pH: [6.0, 7.0], R: [65, 135], M: [45, 68] },
  }
  const spec = defaults[cropName] || defaults.Rice
  return {
    N: rnd(spec.N[0], spec.N[1], 0),
    P: rnd(spec.P[0], spec.P[1], 0),
    K: rnd(spec.K[0], spec.K[1], 0),
    temperature: rnd(spec.T[0], spec.T[1], 1),
    humidity: rnd(spec.H[0], spec.H[1], 0),
    ph: rnd(spec.pH[0], spec.pH[1], 1),
    rainfall: rnd(spec.R[0], spec.R[1], 1),
    soil_moisture: rnd(spec.M[0], spec.M[1], 0),
  }
}

export default function FarmSetupWizard({ currentUser, onFarmConfigured, initialConfig, onSelectCropForDetail }) {
  const [selectedCrop, setSelectedCrop] = useState(initialConfig?.crop || 'Rice')
  const [farmState, setFarmState] = useState(initialConfig?.state || 'Maharashtra')
  const [zoneCount, setZoneCount] = useState(initialConfig?.zones?.length || 3)
  const [areaAcres, setAreaAcres] = useState(initialConfig?.area || 12.5)
  const [zones, setZones] = useState(initialConfig?.zones || [
    { id: 'zone-1', label: 'Zone A', crop: 'Rice', cropName: 'Rice Field', area: '4.0 Ac' },
    { id: 'zone-2', label: 'Zone B', crop: 'Wheat', cropName: 'Wheat Plot', area: '4.5 Ac' },
    { id: 'zone-3', label: 'Zone C', crop: 'Maize', cropName: 'Maize Quadrant', area: '4.0 Ac' },
  ])
  const [isConfiguring, setIsConfiguring] = useState(!initialConfig)

  const handleZoneCountChange = (count) => {
    const val = Math.max(1, Math.min(8, count))
    setZoneCount(val)
    const newZones = []
    for (let i = 0; i < val; i++) {
      const letter = String.fromCharCode(65 + i)
      newZones.push(zones[i] || {
        id: `zone-${i + 1}`,
        label: `Zone ${letter}`,
        crop: selectedCrop,
        cropName: `${selectedCrop} Plot`,
        area: `${(areaAcres / val).toFixed(1)} Ac`,
      })
    }
    setZones(newZones)
  }

  const handleUpdateZoneCrop = (idx, cropName) => {
    const next = [...zones]
    next[idx] = {
      ...next[idx],
      crop: cropName,
      cropName: `${cropName} Field`,
    }
    setZones(next)
  }

  const handleSaveAndDeploy = () => {
    const farmProfile = {
      primaryCrop: selectedCrop,
      state: farmState,
      area: areaAcres,
      zones: zones,
      timestamp: new Date().toISOString(),
    }
    const userKey = currentUser
      ? `agri_farm_profile_${String(currentUser.id || currentUser.email || currentUser.name).toLowerCase().replace(/[^a-z0-9]/g, '_')}`
      : 'agri_active_farm_config'
    localStorage.setItem(userKey, JSON.stringify(farmProfile))
    localStorage.setItem('agri_active_farm_config', JSON.stringify(farmProfile))
    setIsConfiguring(false)
    onFarmConfigured(farmProfile)
  }

  return (
    <div className="modern-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.01em' }}>
            🌾 Cultivated Crop Setup & Field Allocation
          </h3>
          <p style={{ margin: '0.15rem 0 0 0', fontSize: '0.775rem', color: '#64748B' }}>
            Specify active standing crops to automatically generate realistic IoT sensor streams
          </p>
        </div>

        {initialConfig && !isConfiguring && (
          <button
            type="button"
            className="btn-secondary-white"
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
            onClick={() => setIsConfiguring(true)}
          >
            ⚙️ Reconfigure Farm
          </button>
        )}
      </div>

      {isConfiguring ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
          {/* Quick Select Crop Grid */}
          <div>
            <label className="modern-label">1. Primary Target Crop in Cultivation</label>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
              gap: '0.55rem',
              marginTop: '0.35rem',
            }}>
              {CROP_CATALOG.map((item) => {
                const isSel = selectedCrop === item.name
                return (
                  <div
                    key={item.name}
                    onClick={() => {
                      setSelectedCrop(item.name)
                      // update existing zones with this primary crop
                      setZones(prev => prev.map(z => ({ ...z, crop: item.name, cropName: `${item.name} Plot` })))
                    }}
                    style={{
                      border: isSel ? '2px solid #10B981' : '1.5px solid #CBD5BF',
                      backgroundColor: isSel ? '#ECFDF5' : '#FFFFFF',
                      borderRadius: '12px',
                      padding: '0.75rem 0.85rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: isSel ? '0 4px 12px rgba(16, 185, 129, 0.25)' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '1.25rem' }}>{item.icon}</span>
                      <span style={{ fontWeight: 800, fontSize: '0.9rem', color: isSel ? '#065F46' : '#13241B' }}>
                        {item.name}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.675rem', color: '#64748B' }}>
                      Water: {item.waterNeed} · {item.duration}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Region and Area */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.85rem' }}>
            <div>
              <label className="modern-label" htmlFor="farm-state">Agroclimatic State</label>
              <select
                id="farm-state"
                className="modern-select"
                value={farmState}
                onChange={(e) => setFarmState(e.target.value)}
              >
                {STATES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div>
              <label className="modern-label" htmlFor="farm-zones-count">Number of Farm Zones (1–8)</label>
              <input
                id="farm-zones-count"
                type="number"
                min="1"
                max="8"
                className="modern-input"
                value={zoneCount}
                onChange={(e) => handleZoneCountChange(parseInt(e.target.value) || 1)}
              />
            </div>

            <div>
              <label className="modern-label" htmlFor="farm-area">Total Farm Area (Acres)</label>
              <input
                id="farm-area"
                type="number"
                step="0.5"
                min="1"
                className="modern-input"
                value={areaAcres}
                onChange={(e) => setAreaAcres(parseFloat(e.target.value) || 1)}
              />
            </div>
          </div>

          {/* Individual Zone Breakdown */}
          <div>
            <label className="modern-label">Configure Zones & Multi-Crop Diversity</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: '0.65rem', marginTop: '0.35rem' }}>
              {zones.map((z, idx) => (
                <div key={z.id} style={{
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: '8px',
                  padding: '0.65rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, color: '#334155' }}>
                    <span>{z.label}</span>
                    <span style={{ color: '#64748B' }}>{z.area}</span>
                  </div>
                  <select
                    className="modern-select"
                    style={{ padding: '0.4rem 0.5rem', fontSize: '0.8rem' }}
                    value={z.crop}
                    onChange={(e) => handleUpdateZoneCrop(idx, e.target.value)}
                  >
                    {CROP_CATALOG.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                  </select>
                </div>
              ))}
            </div>
          </div>

          <button
            type="button"
            className="btn-primary-emerald"
            style={{ width: '100%', padding: '0.75rem', marginTop: '0.5rem' }}
            onClick={handleSaveAndDeploy}
          >
            ✓ Deploy Farm & Activate Simulated IoT Sensors →
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#F0FDFA', border: '1px solid #CCFBF1', borderRadius: '10px', padding: '0.85rem 1.15rem' }}>
          <div>
            <span style={{ fontSize: '0.725rem', fontWeight: 700, color: '#0F766E', textTransform: 'uppercase' }}>
              Active Cultivation Profile
            </span>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0F172A', marginTop: '0.1rem' }}>
              {selectedCrop} ({farmState}) · {zoneCount} Field Zones ({areaAcres} Acres)
            </div>
            <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: '0.15rem' }}>
              IoT Telemetry Stream: Hardware simulation active across all sectors
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              backgroundColor: '#FFFFFF',
              border: '1px solid #99F6E4',
              color: '#0F766E',
              padding: '0.35rem 0.65rem',
              borderRadius: '999px',
              fontSize: '0.725rem',
              fontWeight: 700,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#0D9488' }} />
              Live Telemetry Linked
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
