import { useEffect, useState } from 'react'
import { farmApi } from '../services/api'

export default function FarmDashboard({ onSelectCropForDetail }) {
  const [zones, setZones] = useState([])
  const [selectedZoneId, setSelectedZoneId] = useState('zone-1')
  const [zoneAdvisory, setZoneAdvisory] = useState(null)
  const [weather, setWeather] = useState(null)
  const [loading, setLoading] = useState(false)
  const [advisoryLoading, setAdvisoryLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState('')
  const [error, setError] = useState('')

  const fetchZones = async () => {
    try {
      const data = await farmApi.zones()
      setZones(data)
    } catch (err) {
      setError(err.message || 'Could not load farm zones')
    }
  }

  const fetchWeather = async () => {
    try {
      const w = await farmApi.weather()
      setWeather(w)
    } catch {
      // Weather fallback is handled gracefully
    }
  }

  const fetchAdvisoryForZone = async (zoneId) => {
    setAdvisoryLoading(true)
    setError('')
    try {
      const adv = await farmApi.advisory(zoneId)
      setZoneAdvisory(adv)
    } catch (err) {
      setError(err.message || 'Could not fetch 360° zone advisory')
    } finally {
      setAdvisoryLoading(false)
    }
  }

  useEffect(() => {
    fetchZones()
    fetchWeather()
    fetchAdvisoryForZone('zone-1')
  }, [])

  const handleSelectZone = (zoneId) => {
    setSelectedZoneId(zoneId)
    fetchAdvisoryForZone(zoneId)
    setActionMessage('')
  }

  const handleSimulate = async (scenario) => {
    setLoading(true)
    setActionMessage('')
    try {
      await farmApi.simulate(selectedZoneId, scenario)
      await fetchZones()
      await fetchAdvisoryForZone(selectedZoneId)
      const labels = {
        dry_spell: 'Simulated 4-day dry spell (moisture dropped, temp rose)',
        monsoon_rain: 'Simulated monsoon rainfall (soil replenished)',
        nutrient_depletion: 'Simulated post-harvest nutrient drawdown (N-P-K lowered)',
        normal: 'Simulated normal day sensor fluctuations',
      }
      setActionMessage(labels[scenario] || 'Sensor values updated.')
    } catch (err) {
      setError(err.message || 'Simulation failed')
    } finally {
      setLoading(false)
    }
  }

  const selectedZone = zones.find((z) => z.id === selectedZoneId) || zones[0]
  const telemetry = selectedZone?.telemetry || {}
  const irrigation = zoneAdvisory?.journey_guidance?.irrigation || selectedZone?.irrigation_summary

  return (
    <section className="farm-dashboard-container" style={{ margin: '0 auto 2.5rem', maxWidth: '1200px' }}>
      {/* Top Header & Agro-Weather Station Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          padding: '1.25rem 1.5rem',
          background: 'var(--card-bg, #1e293b)',
          borderRadius: '12px',
          border: '1px solid var(--border-color, #334155)',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#10b981', fontWeight: 700 }}>
            🌾 Smart Precision Farming Command Center
          </span>
          <h2 style={{ margin: '0.25rem 0 0', fontSize: '1.5rem' }}>
            Multi-Zone IoT Sensor Grid & Autonomous Advisory
          </h2>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem', color: 'var(--muted, #94a3b8)' }}>
            Real-time soil sensors across 5 sectors with automated moisture deficit calculation, pump schedules, and AI agronomy.
          </p>
        </div>

        {weather && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1.25rem',
              background: 'rgba(255,255,255,0.04)',
              padding: '0.75rem 1.25rem',
              borderRadius: '8px',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <div>
              <small style={{ color: 'var(--muted, #94a3b8)', display: 'block', fontSize: '0.75rem' }}>AGRO-METEOROLOGY</small>
              <strong style={{ fontSize: '1.1rem' }}>{weather.temperature_c}°C</strong>
            </div>
            <div>
              <small style={{ color: 'var(--muted, #94a3b8)', display: 'block', fontSize: '0.75rem' }}>HUMIDITY</small>
              <strong style={{ fontSize: '1.1rem' }}>{weather.humidity_pct}%</strong>
            </div>
            <div>
              <small style={{ color: 'var(--muted, #94a3b8)', display: 'block', fontSize: '0.75rem' }}>PRECIPITATION</small>
              <strong style={{ fontSize: '1.1rem' }}>{weather.precipitation_mm} mm</strong>
            </div>
            <div>
              <small style={{ color: 'var(--muted, #94a3b8)', display: 'block', fontSize: '0.75rem' }}>WIND</small>
              <strong style={{ fontSize: '1.1rem' }}>{weather.wind_speed_kmh} km/h</strong>
            </div>
          </div>
        )}
      </div>

      {actionMessage && (
        <div style={{ marginBottom: '1.25rem', padding: '0.75rem 1.25rem', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid #10b981', borderRadius: '8px', color: '#10b981' }}>
          ✓ {actionMessage}
        </div>
      )}

      {error && (
        <div className="request-error" role="alert" style={{ marginBottom: '1.25rem' }}>
          <p>{error}</p>
        </div>
      )}

      {/* 5-Zone Farm Visual Map Grid */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.15rem' }}>🗺️ Farm Map — 5 IoT Sensor Zones</h3>
          <span style={{ fontSize: '0.85rem', color: 'var(--muted, #94a3b8)' }}>Click any zone to inspect sensors & irrigation schedule</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1rem' }}>
          {zones.map((zone) => {
            const isSelected = zone.id === selectedZoneId
            const ir = zone.irrigation_summary || {}
            const statusColor = ir.status_color || '#10b981'
            const moisture = zone.telemetry?.soil_moisture ?? 50

            return (
              <div
                key={zone.id}
                onClick={() => handleSelectZone(zone.id)}
                style={{
                  cursor: 'pointer',
                  padding: '1.1rem',
                  borderRadius: '10px',
                  background: isSelected ? 'rgba(56, 189, 248, 0.12)' : 'var(--card-bg, #1e293b)',
                  border: isSelected ? '2px solid #38bdf8' : '1px solid var(--border-color, #334155)',
                  boxShadow: isSelected ? '0 0 16px rgba(56, 189, 248, 0.2)' : 'none',
                  transition: 'all 0.2s ease',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                {/* Status indicator bar on top */}
                <div style={{ height: '4px', width: '100%', background: statusColor, position: 'absolute', top: 0, left: 0 }} />

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: '0.25rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{zone.name.split('·')[0].trim()}</span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      background: `${statusColor}22`,
                      color: statusColor,
                      border: `1px solid ${statusColor}55`,
                      textTransform: 'uppercase',
                    }}
                  >
                    {ir.status ? ir.status.replace('_', ' ') : 'STABLE'}
                  </span>
                </div>

                <div style={{ margin: '0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1.25rem' }}>
                    {zone.active_crop === 'rice' ? '🌾' : zone.active_crop === 'cotton' ? '☁️' : zone.active_crop === 'maize' ? '🌽' : zone.active_crop === 'banana' ? '🍌' : '🌱'}
                  </span>
                  <div>
                    <strong style={{ fontSize: '1rem', textTransform: 'capitalize' }}>{zone.active_crop}</strong>
                    <div style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>{zone.area_acres} Acres · {zone.soil_type}</div>
                  </div>
                </div>

                {/* Soil Moisture Mini-Gauge */}
                <div style={{ marginTop: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                    <span style={{ color: 'var(--muted, #94a3b8)' }}>Soil Moisture</span>
                    <strong style={{ color: statusColor }}>{moisture}%</strong>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.08)', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${Math.min(100, Math.max(0, moisture))}%`,
                        height: '100%',
                        background: statusColor,
                        borderRadius: '3px',
                      }}
                    />
                  </div>
                </div>

                <div style={{ marginTop: '0.6rem', fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>
                  {zone.irrigation_channel}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Selected Zone Deep Dive: 2-Column Command Station */}
      {selectedZone && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 1.3fr)', gap: '1.5rem', alignItems: 'start' }}>
          {/* Left Column: Live IoT Sensor Telemetry & Simulation Controls */}
          <div style={{ background: 'var(--card-bg, #1e293b)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color, #334155)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div>
                <p className="eyebrow" style={{ margin: 0 }}>Active Zone Telemetry</p>
                <h3 style={{ margin: '0.2rem 0' }}>{selectedZone.name}</h3>
              </div>
              <span style={{ fontSize: '0.8rem', background: '#334155', padding: '0.25rem 0.6rem', borderRadius: '4px', color: '#94a3b8' }}>
                {selectedZone.area_acres} Acres
              </span>
            </div>

            {/* 8 Sensor Value Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>🌱 Nitrogen (N)</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>{telemetry.N} <small style={{ fontSize: '0.7rem' }}>kg/ha</small></div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>🧪 Phosphorus (P)</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>{telemetry.P} <small style={{ fontSize: '0.7rem' }}>kg/ha</small></div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>💎 Potassium (K)</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>{telemetry.K} <small style={{ fontSize: '0.7rem' }}>kg/ha</small></div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>🌊 Soil Moisture</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: irrigation?.status_color || '#10b981' }}>
                  {telemetry.soil_moisture}%
                </div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>🌡️ Temperature</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{telemetry.temperature}°C</div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>💧 Humidity</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{telemetry.humidity}%</div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>⚖️ Soil pH</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{telemetry.ph}</div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>🌧️ Rainfall</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{telemetry.rainfall} <small style={{ fontSize: '0.7rem' }}>mm</small></div>
              </div>
            </div>

            {/* IoT Scenario Simulation Station */}
            <div style={{ borderTop: '1px solid var(--border-color, #334155)', paddingTop: '1rem' }}>
              <p className="eyebrow" style={{ margin: '0 0 0.5rem' }}>IoT Sensor Simulation (Test What-Ifs)</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
                <button
                  type="button"
                  className="tab-btn"
                  style={{ padding: '0.5rem', fontSize: '0.75rem' }}
                  onClick={() => handleSimulate('dry_spell')}
                  disabled={loading}
                >
                  ☀️ Dry Spell / Heat
                </button>
                <button
                  type="button"
                  className="tab-btn"
                  style={{ padding: '0.5rem', fontSize: '0.75rem' }}
                  onClick={() => handleSimulate('monsoon_rain')}
                  disabled={loading}
                >
                  🌧️ Heavy Monsoon
                </button>
                <button
                  type="button"
                  className="tab-btn"
                  style={{ padding: '0.5rem', fontSize: '0.75rem' }}
                  onClick={() => handleSimulate('nutrient_depletion')}
                  disabled={loading}
                >
                  📉 N-P-K Drawdown
                </button>
                <button
                  type="button"
                  className="tab-btn"
                  style={{ padding: '0.5rem', fontSize: '0.75rem' }}
                  onClick={() => handleSimulate('normal')}
                  disabled={loading}
                >
                  🔄 Normal Shift
                </button>
              </div>
              <small style={{ display: 'block', marginTop: '0.5rem', color: 'var(--muted, #94a3b8)', fontSize: '0.7rem' }}>
                Hardware note: Real ESP32 / Arduino sensors push live readings to <code style={{ color: '#38bdf8' }}>POST /api/v1/farm/zones/{selectedZone.id}/telemetry</code>.
              </small>
            </div>
          </div>

          {/* Right Column: Complete Farmer Journey Guidance (Irrigation + Crop + Fertilizer + Pest) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* 1. Smart Irrigation Action Card */}
            {irrigation && (
              <div
                style={{
                  background: 'var(--card-bg, #1e293b)',
                  padding: '1.5rem',
                  borderRadius: '12px',
                  border: `2px solid ${irrigation.status_color || '#10b981'}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: irrigation.status_color, fontWeight: 700 }}>
                      SMART IRRIGATION CONTROLLER
                    </span>
                    <h3 style={{ margin: '0.25rem 0', color: irrigation.status_color }}>
                      {irrigation.status === 'CRITICAL_DEFICIT' ? '🚨 CRITICAL WATER DEFICIT' :
                       irrigation.status === 'MODERATE_DEFICIT' ? '⚠️ MODERATE IRRIGATION NEEDED' :
                       irrigation.status === 'WATERLOGGED' ? '🌊 DRAINAGE REQUIRED' :
                       '✅ OPTIMAL SOIL MOISTURE'}
                    </h3>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--muted, #94a3b8)' }}>Urgency</span>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: irrigation.status_color }}>{irrigation.urgency}</div>
                  </div>
                </div>

                <p style={{ margin: '0.75rem 0', fontSize: '0.92rem', lineHeight: '1.4' }}>
                  {irrigation.action}
                </p>

                {/* Irrigation Specs & Pump runtime */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                    gap: '0.75rem',
                    background: 'rgba(255,255,255,0.03)',
                    padding: '0.85rem',
                    borderRadius: '8px',
                    margin: '0.75rem 0',
                  }}
                >
                  <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--muted, #94a3b8)' }}>Optimal Moisture</span>
                    <div style={{ fontWeight: 600 }}>{irrigation.optimal_range_pct?.[0]}% - {irrigation.optimal_range_pct?.[1]}%</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--muted, #94a3b8)' }}>Moisture Deficit</span>
                    <div style={{ fontWeight: 600, color: irrigation.status_color }}>
                      {irrigation.moisture_deficit_pct > 0 ? `-${irrigation.moisture_deficit_pct}%` : 'None'}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--muted, #94a3b8)' }}>Water Volume</span>
                    <div style={{ fontWeight: 600 }}>
                      {irrigation.water_volume_liters ? `${irrigation.water_volume_liters.toLocaleString()} L` : '0 L'}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--muted, #94a3b8)' }}>Pump Runtime (5 HP)</span>
                    <div style={{ fontWeight: 600 }}>
                      {irrigation.estimated_pump_runtime_hours ? `${irrigation.estimated_pump_runtime_hours} hrs` : 'Off'}
                    </div>
                  </div>
                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--muted, #94a3b8)' }}>
                  💡 <b>Recommended Method:</b> {irrigation.recommended_method} ({irrigation.water_sensitivity} sensitivity)
                </div>
              </div>
            )}

            {/* 2. Crop AI & Fertilizer Guidance */}
            <div style={{ background: 'var(--card-bg, #1e293b)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color, #334155)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <p className="eyebrow" style={{ margin: 0 }}>Farming Journey: Crop & Nutrient Plan</p>
                {advisoryLoading && <span style={{ fontSize: '0.8rem', color: '#38bdf8' }}>Analyzing sensors...</span>}
              </div>

              {/* Crop ranking preview */}
              <div style={{ marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '0.4rem' }}>
                  🌱 AI Crop Recommendation for this exact soil & weather:
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {zoneAdvisory?.journey_guidance?.crop_suitability?.ranked_alternatives?.map((item, idx) => (
                    <span
                      key={idx}
                      style={{
                        padding: '0.3rem 0.75rem',
                        borderRadius: '20px',
                        background: item.crop.toLowerCase() === selectedZone.active_crop.toLowerCase() ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255,255,255,0.06)',
                        border: item.crop.toLowerCase() === selectedZone.active_crop.toLowerCase() ? '1px solid #22c55e' : '1px solid rgba(255,255,255,0.1)',
                        fontSize: '0.82rem',
                        fontWeight: item.crop.toLowerCase() === selectedZone.active_crop.toLowerCase() ? 700 : 400,
                      }}
                    >
                      #{idx + 1} {item.crop} ({((item.probability || item.confidence || 0.8) * 100).toFixed(0)}%)
                      {item.crop.toLowerCase() === selectedZone.active_crop.toLowerCase() && ' · Active'}
                    </span>
                  ))}
                </div>
              </div>

              {/* Fertilizer prescription */}
              {zoneAdvisory?.journey_guidance?.fertilizer && (
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', color: '#f59e0b', marginBottom: '0.25rem' }}>
                    🧪 Fertilizer Top-Up Prescription:
                  </span>
                  <div style={{ fontSize: '0.85rem', lineHeight: '1.4' }}>
                    {zoneAdvisory.journey_guidance.fertilizer.fertilizer_name ? (
                      <>
                        Recommended Product: <b>{zoneAdvisory.journey_guidance.fertilizer.fertilizer_name}</b> (
                        {zoneAdvisory.journey_guidance.fertilizer.estimated_bags_50kg} bags for {selectedZone.area_acres} acres)
                      </>
                    ) : (
                      'N-P-K balance is within standard agronomic maintenance limits.'
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* 3. Pest Early Warning Card */}
            {zoneAdvisory?.journey_guidance?.pest_protection && (
              <div style={{ background: 'var(--card-bg, #1e293b)', padding: '1.25rem', borderRadius: '12px', border: '1px solid var(--border-color, #334155)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ef4444' }}>
                    🐛 Pest Outbreak Risk · {selectedZone.active_crop.toUpperCase()}
                  </span>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      background: zoneAdvisory.journey_guidance.pest_protection.risk_assessment?.risk_level === 'High' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                      color: zoneAdvisory.journey_guidance.pest_protection.risk_assessment?.risk_level === 'High' ? '#ef4444' : '#f59e0b',
                    }}
                  >
                    {zoneAdvisory.journey_guidance.pest_protection.risk_assessment?.risk_level || 'Moderate'} Threat
                  </span>
                </div>
                <div style={{ fontSize: '0.82rem', marginTop: '0.4rem', color: 'var(--muted, #94a3b8)' }}>
                  <b>Primary Pest:</b> {zoneAdvisory.journey_guidance.pest_protection.primary_pest}
                </div>
                <div style={{ fontSize: '0.82rem', marginTop: '0.25rem' }}>
                  <b>Organic Control:</b> {zoneAdvisory.journey_guidance.pest_protection.organic_control}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
