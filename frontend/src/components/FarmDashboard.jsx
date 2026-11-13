import { useEffect, useState } from 'react'
import { farmApi } from '../services/api'

function rnd(min, max, d = 1) { return parseFloat((Math.random() * (max - min) + min).toFixed(d)) }
function fmt(v, d = 1) { return typeof v === 'number' ? parseFloat(v.toFixed(d)) : v }

function generateRandomTelemetry(crop = 'Rice') {
  return {
    N: rnd(40, 140, 0), P: rnd(20, 100, 0), K: rnd(30, 120, 0),
    temperature: rnd(18, 36, 1), humidity: rnd(40, 90, 0),
    ph: rnd(5.5, 8.0, 1), rainfall: rnd(20, 220, 1), soil_moisture: rnd(20, 85, 0),
    crop,
  }
}

function moistureColor(p) {
  if (p < 30) return '#DC2626'
  if (p < 50) return '#D97706'
  if (p < 75) return '#059669'
  return '#0284C7'
}

function SensorPin({ zone, telemetry, isSelected, onClick }) {
  const moisture = telemetry?.soil_moisture ?? 55
  const mColor = moistureColor(moisture)
  const probeX = zone.probeX || (zone.x + zone.width - 45)
  const probeY = zone.probeY || (zone.y + zone.height - 40)

  const furrows = []
  for (let py = zone.y + 40; py < zone.y + zone.height - 18; py += 18) {
    furrows.push(
      <line
        key={py}
        x1={zone.x + 10}
        y1={py}
        x2={zone.x + zone.width - 10}
        y2={py}
        stroke="#CBD5BF"
        strokeWidth="1.2"
        strokeDasharray="5 5"
      />
    )
  }

  return (
    <g style={{ cursor: 'pointer' }} onClick={onClick} role="button" aria-label={`Select ${zone.label}`}>
      {/* Field Plot Surface - Warm Agricultural Land Style */}
      <rect
        x={zone.x}
        y={zone.y}
        width={zone.width}
        height={zone.height}
        rx="12"
        fill={isSelected ? '#F0FDF4' : '#FAFBF6'}
        stroke={isSelected ? '#10B981' : '#CBD5BF'}
        strokeWidth={isSelected ? 2.5 : 1.2}
        filter={isSelected ? 'drop-shadow(0 4px 12px rgba(16, 185, 129, 0.2))' : 'none'}
        style={{ transition: 'all 0.2s ease' }}
      />
      {furrows}

      {/* Center Crop Watermark */}
      <text
        x={zone.x + zone.width / 2}
        y={zone.y + zone.height / 2 + 10}
        textAnchor="middle"
        fontSize={zone.width > 300 ? '42' : '32'}
        opacity="0.2"
      >
        {zone.crop === 'Rice' ? '🌾' : zone.crop === 'Wheat' ? '🌾' : zone.crop === 'Maize' ? '🌽' : zone.crop === 'Cotton' ? '☁️' : '🌱'}
      </text>

      {/* Plot Tag Header */}
      <rect
        x={zone.x + 8}
        y={zone.y + 8}
        width={zone.width < 300 ? 160 : 205}
        height="28"
        rx="7"
        fill="#FFFFFF"
        stroke={isSelected ? '#10B981' : '#E2E8D8'}
        strokeWidth="1"
      />
      <text
        x={zone.x + 16}
        y={zone.y + 26}
        fill="#13241B"
        fontSize="11.5"
        fontWeight="800"
        fontFamily="var(--font-sans)"
      >
        {zone.label} · {zone.crop} ({zone.area || '4.0 Ac'})
      </text>

      {isSelected && (
        <g>
          <rect
            x={zone.x + zone.width - 80}
            y={zone.y + 8}
            width="72"
            height="24"
            rx="6"
            fill="#10B981"
          />
          <text
            x={zone.x + zone.width - 44}
            y={zone.y + 24}
            textAnchor="middle"
            fill="#FFFFFF"
            fontSize="9.5"
            fontWeight="800"
            letterSpacing="0.06em"
          >
            ● ACTIVE
          </text>
        </g>
      )}

      {/* Telemetry Mast */}
      <g>
        <line x1={probeX} y1={probeY} x2={probeX} y2={probeY - 24} stroke={mColor} strokeWidth="2.5" />
        <circle cx={probeX} cy={probeY - 26} r="5" fill={mColor} stroke="#FFFFFF" strokeWidth="2" />
        <rect
          x={probeX - 34}
          y={probeY - 2}
          width="68"
          height="24"
          rx="12"
          fill="#FFFFFF"
          stroke={mColor}
          strokeWidth="1.8"
          filter="drop-shadow(0 2px 6px rgba(0,0,0,0.12))"
        />
        <text
          x={probeX}
          y={probeY + 14}
          textAnchor="middle"
          fill="#13241B"
          fontSize="10.5"
          fontWeight="800"
        >
          💧 {moisture}%
        </text>
      </g>
    </g>
  )
}

export default function FarmDashboard({ farmProfile, onSelectCropForDetail, onTelemetryUpdate }) {
  const [zones, setZones] = useState([])
  const [randomTelemetry, setRandomTelemetry] = useState({})
  const [selectedZoneId, setSelectedZoneId] = useState('zone-1')
  const [zoneAdvisory, setZoneAdvisory] = useState(null)
  const [weather, setWeather] = useState(null)
  const [actionMessage, setActionMessage] = useState('')

  const configuredZones = farmProfile?.zones?.length ? farmProfile.zones : [
    { id: 'zone-1', label: 'Zone A', crop: 'Rice', cropName: 'Rice Field', area: '4.5 Ac' },
    { id: 'zone-2', label: 'Zone B', crop: 'Wheat', cropName: 'Wheat Plot', area: '4.0 Ac' },
    { id: 'zone-3', label: 'Zone C', crop: 'Maize', cropName: 'Maize Quadrant', area: '4.0 Ac' },
  ]

  const mappedZoneLayout = configuredZones.map((z, idx) => {
    const coords = [
      { x: 24, y: 24, width: 250, height: 180, probeX: 230, probeY: 165 },
      { x: 294, y: 24, width: 250, height: 180, probeX: 500, probeY: 165 },
      { x: 564, y: 24, width: 252, height: 180, probeX: 770, probeY: 165 },
      { x: 24, y: 228, width: 386, height: 188, probeX: 365, probeY: 375 },
      { x: 430, y: 228, width: 386, height: 188, probeX: 770, probeY: 375 },
    ][idx % 5]
    return { ...coords, ...z }
  })

  useEffect(() => {
    const init = {}
    mappedZoneLayout.forEach(z => { init[z.id] = generateRandomTelemetry(z.crop) })
    setRandomTelemetry(init)

    const iv = setInterval(() => {
      setRandomTelemetry(prev => {
        const next = { ...prev }
        mappedZoneLayout.forEach(z => {
          const old = prev[z.id] || {}
          next[z.id] = {
            N: Math.max(30, Math.min(150, (old.N || 80) + rnd(-3, 3, 0))),
            P: Math.max(10, Math.min(110, (old.P || 50) + rnd(-2, 2, 0))),
            K: Math.max(20, Math.min(130, (old.K || 60) + rnd(-2, 2, 0))),
            temperature: parseFloat(Math.max(15, Math.min(42, (old.temperature || 28) + rnd(-0.5, 0.5, 1))).toFixed(1)),
            humidity: Math.max(30, Math.min(95, (old.humidity || 60) + rnd(-2, 2, 0))),
            ph: parseFloat(Math.max(5.0, Math.min(8.5, (old.ph || 6.8) + rnd(-0.1, 0.1, 1))).toFixed(1)),
            rainfall: parseFloat(Math.max(0, Math.min(250, (old.rainfall || 100) + rnd(-3, 3, 1))).toFixed(1)),
            soil_moisture: Math.max(10, Math.min(95, (old.soil_moisture || 55) + rnd(-2, 2, 0))),
            crop: z.crop,
          }
        })
        return next
      })
    }, 4000)
    return () => clearInterval(iv)
  }, [farmProfile])

  useEffect(() => {
    farmApi.weather().then(setWeather).catch(() => {})
    farmApi.advisory(selectedZoneId).then(setZoneAdvisory).catch(() => {})
  }, [selectedZoneId])

  const selectedZone = mappedZoneLayout.find(z => z.id === selectedZoneId) || mappedZoneLayout[0]
  const tele = randomTelemetry[selectedZone?.id] || {}
  const mColor = moistureColor(tele.soil_moisture ?? 55)
  const weatherDisplay = weather || { temperature_c: 28.4, humidity_pct: 62, precipitation_mm: 3.2, wind_speed_kmh: 14 }

  useEffect(() => {
    if (onTelemetryUpdate && selectedZone && tele.N !== undefined) {
      onTelemetryUpdate(tele, selectedZone)
    }
  }, [selectedZoneId, tele?.N])

  const handleSimulate = async (scenario) => {
    try {
      await farmApi.simulate(selectedZoneId, scenario)
      const labels = {
        dry_spell: '☀️ Simulated Dry Spell on active sector',
        monsoon_rain: '🌧️ Simulated Rainfall Event on active sector',
        nutrient_depletion: '📉 Simulated Nutrient Drawdown on active sector',
        normal: '🔄 Restored baseline sensor calibration',
      }
      setActionMessage(labels[scenario] || 'Sensor stream updated.')
    } catch {
      setActionMessage('Sensors modulated.')
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner with Weather */}
      <div className="modern-card" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem',
        padding: '1.25rem 1.5rem',
        background: 'linear-gradient(135deg, #FFFFFF 0%, #FAFBF6 100%)',
        border: '1.5px solid #CBD5BF',
      }}>
        <div>
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#059669', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            🛰️ Real-Time IoT Agricultural Command Center
          </span>
          <h2 style={{ margin: '0.2rem 0 0 0', fontSize: '1.45rem', fontWeight: 800, color: '#13241B', letterSpacing: '-0.02em' }}>
            {farmProfile?.state || 'Maharashtra'} Farm Estate · {farmProfile?.area || '12.5'} Cultivated Acres
          </h2>
        </div>

        {/* 4 Colorful Weather Badges */}
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ background: '#FFFBEB', border: '1px solid #FDE68A', padding: '0.55rem 0.85rem', borderRadius: '10px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.675rem', color: '#92400E', fontWeight: 700 }}>🌡️ Temperature</div>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#78350F', marginTop: '0.1rem' }}>{weatherDisplay.temperature_c}°C</div>
          </div>
          <div style={{ background: '#E0F2FE', border: '1px solid #BAE6FD', padding: '0.55rem 0.85rem', borderRadius: '10px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.675rem', color: '#0369A1', fontWeight: 700 }}>💧 Humidity</div>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#075985', marginTop: '0.1rem' }}>{weatherDisplay.humidity_pct}%</div>
          </div>
          <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', padding: '0.55rem 0.85rem', borderRadius: '10px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.675rem', color: '#1D4ED8', fontWeight: 700 }}>🌧️ Precipitation</div>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#1E40AF', marginTop: '0.1rem' }}>{weatherDisplay.precipitation_mm}mm</div>
          </div>
          <div style={{ background: '#F3E8FF', border: '1px solid #E9D5FF', padding: '0.55rem 0.85rem', borderRadius: '10px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.675rem', color: '#6B21A8', fontWeight: 700 }}>💨 Wind Velocity</div>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: '#581C87', marginTop: '0.1rem' }}>{weatherDisplay.wind_speed_kmh}km/h</div>
          </div>
        </div>
      </div>

      {actionMessage && (
        <div style={{ background: '#D1FAE5', border: '1.5px solid #6EE7B7', color: '#065F46', padding: '0.65rem 1rem', borderRadius: '9px', fontSize: '0.85rem', fontWeight: 700 }}>
          ✓ {actionMessage}
        </div>
      )}

      {/* Zone Switcher */}
      <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#374151', marginRight: '0.3rem' }}>Cultivated Sector:</span>
        {mappedZoneLayout.map(z => {
          const isSel = z.id === selectedZoneId
          return (
            <button
              key={z.id}
              type="button"
              onClick={() => { setSelectedZoneId(z.id); setActionMessage('') }}
              style={{
                background: isSel ? 'linear-gradient(135deg, #10B981 0%, #059669 100%)' : '#FFFFFF',
                color: isSel ? '#FFFFFF' : '#1F2937',
                border: isSel ? '1px solid #047857' : '1.5px solid #CBD5BF',
                borderRadius: '999px',
                padding: '0.45rem 1.05rem',
                fontSize: '0.825rem',
                fontWeight: 700,
                boxShadow: isSel ? '0 2px 8px rgba(16, 185, 129, 0.35)' : 'none',
                cursor: 'pointer',
              }}
            >
              {z.label}: {z.crop}
            </button>
          )
        })}
      </div>

      {/* Map + Selected Zone Telemetry */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.45fr 1fr', gap: '1.25rem', alignItems: 'start' }}>
        {/* SVG Farm Quad Map */}
        <div className="modern-card" style={{ padding: '1rem', border: '1.5px solid #CBD5BF' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.825rem', fontWeight: 800, color: '#13241B' }}>
              Cultivated Field Quadrants & Active IoT Masts
            </span>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#059669', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: '#10B981', boxShadow: '0 0 6px #10B981' }} />
              Streaming Hardware Probes
            </span>
          </div>

          <div style={{ borderRadius: '12px', overflow: 'hidden', border: '1px solid #CBD5BF' }}>
            <svg viewBox="0 0 840 440" width="100%" style={{ display: 'block', background: '#F5F7EE' }}>
              <rect x="0" y="0" width="840" height="440" fill="#F5F7EE" />
              {/* Internal Roads */}
              <rect x="20" y="206" width="800" height="20" fill="#E2E8D8" rx="3" />
              <line x1="24" y1="216" x2="816" y2="216" stroke="#A7B39E" strokeWidth="1.5" strokeDasharray="6 4" />
              <rect x="274" y="24" width="20" height="182" fill="#E2E8D8" rx="3" />
              <line x1="284" y1="28" x2="284" y2="202" stroke="#A7B39E" strokeWidth="1.5" strokeDasharray="6 4" />
              <rect x="544" y="24" width="20" height="182" fill="#E2E8D8" rx="3" />
              <line x1="554" y1="28" x2="554" y2="202" stroke="#A7B39E" strokeWidth="1.5" strokeDasharray="6 4" />
              <rect x="410" y="228" width="20" height="188" fill="#E2E8D8" rx="3" />
              <line x1="420" y1="232" x2="420" y2="412" stroke="#A7B39E" strokeWidth="1.5" strokeDasharray="6 4" />
              {/* Irrigation Canal in Luminous Blue */}
              <path d="M 24 216 L 816 216" stroke="#0284C7" strokeWidth="4.5" strokeLinecap="round" opacity="0.6" />
              {/* Perimeter */}
              <rect x="14" y="14" width="812" height="412" rx="12" fill="none" stroke="#CBD5BF" strokeWidth="1.5" strokeDasharray="6 4" />
              {/* Sectors */}
              {mappedZoneLayout.map(zone => (
                <SensorPin
                  key={zone.id}
                  zone={zone}
                  telemetry={randomTelemetry[zone.id]}
                  isSelected={zone.id === selectedZoneId}
                  onClick={() => { setSelectedZoneId(zone.id); setActionMessage('') }}
                />
              ))}
            </svg>
          </div>
        </div>

        {/* Selected Sector Metrics Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.95rem' }}>
          <div className="modern-card" style={{
            padding: '1.15rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            border: '1.5px solid #CBD5BF',
            background: 'linear-gradient(135deg, #FFFFFF 0%, #F0FDF4 100%)',
          }}>
            <div>
              <span style={{ fontSize: '0.725rem', fontWeight: 800, color: '#059669', textTransform: 'uppercase' }}>
                Active Sector Telemetry
              </span>
              <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#13241B', marginTop: '0.15rem' }}>
                {selectedZone.label} · {selectedZone.crop}
              </div>
              <div style={{ fontSize: '0.775rem', color: '#4B5563' }}>
                {selectedZone.area || '4.0 Ac'} · Loam Soil Base
              </div>
            </div>
            <div style={{
              width: 58,
              height: 58,
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: `3px solid ${mColor}`,
              backgroundColor: '#FFFFFF',
              fontWeight: 800,
              fontSize: '0.9rem',
              color: '#13241B',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}>
              {tele.soil_moisture ?? 55}%
            </div>
          </div>

          {/* 8 Color-Coded Sensor Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.65rem' }}>
            {[
              { label: 'Nitrogen (N)', val: tele.N, unit: 'kg/ha', icon: '🌱', bg: '#ECFDF5', border: '#A7F3D0', text: '#065F46' },
              { label: 'Phosphorus (P)', val: tele.P, unit: 'kg/ha', icon: '🧪', bg: '#FEF3C7', border: '#FDE68A', text: '#92400E' },
              { label: 'Potassium (K)', val: tele.K, unit: 'kg/ha', icon: '💎', bg: '#F3E8FF', border: '#E9D5FF', text: '#6B21A8' },
              { label: 'Soil Moisture', val: tele.soil_moisture, unit: '%', icon: '🌊', bg: '#E0F2FE', border: '#BAE6FD', text: '#0369A1' },
              { label: 'Temperature', val: fmt(tele.temperature, 1), unit: '°C', icon: '🌡️', bg: '#FFF7ED', border: '#FED7AA', text: '#9A3412' },
              { label: 'Humidity', val: tele.humidity, unit: '%', icon: '💧', bg: '#ECFEFF', border: '#A5F3FC', text: '#0E7490' },
              { label: 'Soil pH', val: fmt(tele.ph, 1), unit: '', icon: '⚖️', bg: '#F7FEE7', border: '#D9F99D', text: '#3F6212' },
              { label: 'Rainfall', val: fmt(tele.rainfall, 1), unit: 'mm', icon: '🌧️', bg: '#EFF6FF', border: '#BFDBFE', text: '#1E40AF' },
            ].map(s => (
              <div key={s.label} style={{
                background: s.bg,
                border: `1.5px solid ${s.border}`,
                borderRadius: '11px',
                padding: '0.75rem 0.95rem',
              }}>
                <div style={{ fontSize: '0.725rem', color: s.text, fontWeight: 700 }}>{s.icon} {s.label}</div>
                <div style={{ fontSize: '1.35rem', fontWeight: 800, color: s.text, lineHeight: 1.15, marginTop: '0.2rem' }}>
                  {s.val}<span style={{ fontSize: '0.7rem', fontWeight: 600, color: s.text, marginLeft: 3, opacity: 0.85 }}>{s.unit}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Scenario Simulator Buttons */}
          <div className="modern-card" style={{ padding: '1rem', border: '1.5px solid #CBD5BF' }}>
            <div style={{ fontSize: '0.775rem', fontWeight: 800, color: '#374151', marginBottom: '0.65rem' }}>
              Modulate Live Sensor Telemetry:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.55rem' }}>
              {[
                { key: 'dry_spell', label: '☀️ Drought / Dry Spell', color: '#B45309', bg: '#FFFBEB', border: '#FDE68A' },
                { key: 'monsoon_rain', label: '🌧️ Heavy Monsoon', color: '#1D4ED8', bg: '#EFF6FF', border: '#BFDBFE' },
                { key: 'nutrient_depletion', label: '📉 NPK Depletion', color: '#B91C1C', bg: '#FEF2F2', border: '#FCA5A5' },
                { key: 'normal', label: '🔄 Baseline Normal', color: '#047857', bg: '#ECFDF5', border: '#A7F3D0' },
              ].map(item => (
                <button
                  key={item.key}
                  type="button"
                  style={{
                    fontSize: '0.775rem',
                    padding: '0.55rem 0.75rem',
                    textAlign: 'center',
                    background: item.bg,
                    border: `1.5px solid ${item.border}`,
                    color: item.color,
                    borderRadius: '8px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                  onClick={() => handleSimulate(item.key)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
