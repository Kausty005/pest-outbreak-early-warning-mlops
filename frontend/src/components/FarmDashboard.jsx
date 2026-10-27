import { useEffect, useState } from 'react'
import { farmApi } from '../services/api'

function rnd(min, max, d = 1) { return parseFloat((Math.random() * (max - min) + min).toFixed(d)) }
function fmt(v, d = 1) { return typeof v === 'number' ? parseFloat(v.toFixed(d)) : v }

function generateRandomTelemetry() {
  return {
    N: rnd(40, 140, 0), P: rnd(20, 100, 0), K: rnd(30, 120, 0),
    temperature: rnd(18, 38, 1), humidity: rnd(35, 90, 0),
    ph: rnd(5.5, 8.2, 1), rainfall: rnd(0, 220, 1), soil_moisture: rnd(15, 85, 0),
  }
}

function moistureColor(p) {
  if (p < 30) return '#ef4444'
  if (p < 50) return '#f59e0b'
  if (p < 75) return '#10b981'
  return '#38bdf8'
}

// Farmer-readable insight generators
function nitrogenInsight(n) {
  if (n < 50) return { status: 'Low', color: '#ef4444', advice: 'Nitrogen is critically low. Apply Urea (46-0-0) at 60 kg/acre immediately. Yellowing of older leaves is a warning sign. Without N, your crop cannot produce chlorophyll and yield will drop 30-50%.' }
  if (n < 80) return { status: 'Moderate', color: '#f59e0b', advice: 'Nitrogen is slightly below optimal. Apply a split dose of DAP fertilizer. Aim for 80-120 kg/ha for most cereal crops. Monitor leaf color — should be a rich dark green.' }
  if (n <= 120) return { status: 'Optimal', color: '#10b981', advice: 'Nitrogen levels are in the optimal range. Your crop has sufficient N for healthy vegetative growth. No immediate action needed. Continue monitoring weekly.' }
  return { status: 'Excess', color: '#38bdf8', advice: 'Nitrogen is too high — this can cause excessive leaf growth at the cost of grain/fruit. Skip N fertilizer for 2-3 weeks. Excess N can also increase pest susceptibility and leach into groundwater.' }
}

function phosphorusInsight(p) {
  if (p < 25) return { status: 'Low', color: '#ef4444', advice: 'Phosphorus is deficient. Apply DAP (18-46-0) or SSP fertilizer. P is critical for root development, flowering, and seed formation. Purple/reddish leaf discoloration is a warning sign.' }
  if (p < 50) return { status: 'Moderate', color: '#f59e0b', advice: 'Phosphorus is adequate but could be improved. Apply superphosphate at transplanting stage. P availability drops in acidic soils — check your pH reading.' }
  if (p <= 80) return { status: 'Optimal', color: '#10b981', advice: 'Phosphorus levels are good. Your crop has enough P for strong root system and energy transfer. No immediate action needed.' }
  return { status: 'Excess', color: '#38bdf8', advice: 'High phosphorus can lock out zinc and iron. Avoid P fertilizers for this season. Excess P can run off into water bodies causing algal blooms.' }
}

function potassiumInsight(k) {
  if (k < 35) return { status: 'Low', color: '#ef4444', advice: 'Potassium deficiency detected. Apply MOP (Muriate of Potash) at 40 kg/acre. K strengthens plant cell walls, improves drought resistance, and enhances fruit/grain quality. Brown leaf edges are a warning sign.' }
  if (k < 60) return { status: 'Moderate', color: '#f59e0b', advice: 'Potassium is slightly low. Apply potash fertilizer or wood ash. K is especially important during grain-filling stage — inadequate K reduces quality and post-harvest shelf life.' }
  if (k <= 100) return { status: 'Optimal', color: '#10b981', advice: 'Potassium is in good range. Your crop has adequate K for stress tolerance, disease resistance, and quality yield. No action needed.' }
  return { status: 'Excess', color: '#38bdf8', advice: 'Very high K can interfere with calcium and magnesium uptake. Hold off on potash applications. Excess K rarely causes direct toxicity but imbalances secondary nutrients.' }
}

function moistureInsight(m) {
  if (m < 25) return { status: 'Critical Dry', color: '#ef4444', advice: 'URGENT: Soil is extremely dry. Irrigate immediately — crops under this stress for more than 48 hours will suffer permanent wilting and yield loss. Run drip/sprinkler system for at least 3-4 hours.' }
  if (m < 45) return { status: 'Needs Water', color: '#f59e0b', advice: 'Soil moisture is below the stress threshold. Schedule irrigation within the next 24 hours. Water in the early morning (5-7 AM) to minimize evaporation. Use drip irrigation for 60% efficiency gain over flood irrigation.' }
  if (m < 70) return { status: 'Optimal', color: '#10b981', advice: 'Soil moisture is in the ideal range for most crops. Roots can access water freely. No irrigation needed today. Check again in 2-3 days or after any hot/windy day.' }
  return { status: 'Waterlogged', color: '#38bdf8', advice: 'Soil is over-saturated. Stop all irrigation. Open drainage channels if available. Waterlogged roots cannot breathe (anaerobic conditions), leading to root rot within 24-48 hours in most crops.' }
}

function temperatureInsight(t) {
  if (t < 15) return { status: 'Too Cold', color: '#38bdf8', advice: 'Temperature is too low for active crop growth. Most tropical crops stop growing below 15°C. Consider row covers or polytunnel. Delay transplanting until temperatures rise.' }
  if (t < 22) return { status: 'Cool', color: '#a78bfa', advice: 'Cool temperatures slow growth but are acceptable for wheat, mustard, and leafy vegetables. Monitor for fungal diseases which thrive in cool-moist conditions.' }
  if (t <= 32) return { status: 'Optimal', color: '#10b981', advice: 'Temperature is in the ideal range for most crops (20-32°C). Photosynthesis and nutrient uptake are at their peak. Maintain soil moisture to sustain these optimal growing conditions.' }
  if (t <= 38) return { status: 'Hot', color: '#f59e0b', advice: 'High temperature is causing heat stress. Increase irrigation frequency (water in evening too). Consider light mulching to cool the soil. Flowers may drop if temperature stays above 35°C during flowering stage.' }
  return { status: 'Extreme Heat', color: '#ef4444', advice: 'DANGER: Extreme heat (>38°C) causes protein denaturation in crops. Emergency irrigation 2x daily. Apply kaolin clay spray as reflective coating. Shade nets can reduce canopy temperature by 4-6°C.' }
}

function humidityInsight(h) {
  if (h < 40) return { status: 'Too Dry', color: '#f59e0b', advice: 'Very low humidity increases plant transpiration and water stress. Irrigation demand will spike. Watch for spider mites and thrips — these pests thrive in dry conditions.' }
  if (h <= 70) return { status: 'Optimal', color: '#10b981', advice: 'Humidity is in the comfortable range. Good for most crops. Pollination and grain filling work best in 50-70% RH. Continue normal monitoring.' }
  if (h <= 85) return { status: 'High', color: '#f59e0b', advice: 'High humidity increases risk of fungal diseases (late blight, powdery mildew, downy mildew). Ensure proper spacing for air circulation. Avoid evening irrigation which keeps foliage wet overnight.' }
  return { status: 'Very High', color: '#ef4444', advice: 'ALERT: Extremely high humidity creates perfect conditions for fungal outbreaks. Apply preventive fungicide (Mancozeb or Copper-based) immediately. Inspect leaves for early signs of blight or mold.' }
}

function phInsight(ph) {
  if (ph < 5.5) return { status: 'Very Acidic', color: '#ef4444', advice: 'Soil is too acidic. Apply agricultural lime (CaCO3) at 2-4 tonnes/ha. Acidic soil locks out phosphorus, calcium and magnesium. Most crops prefer 6.0-7.0 pH. Allow 4-6 weeks for lime to react.' }
  if (ph < 6.0) return { status: 'Slightly Acidic', color: '#f59e0b', advice: 'Mildly acidic — acceptable for rice and most vegetables but slightly reduces P availability. Apply dolomite lime at half rate. Acidic conditions also favor aluminum toxicity in some soils.' }
  if (ph <= 7.2) return { status: 'Optimal', color: '#10b981', advice: 'pH is in the ideal range (6.0-7.2) for most crops. Nutrients are maximally available to roots at this pH. No pH adjustment needed.' }
  if (ph <= 8.0) return { status: 'Alkaline', color: '#f59e0b', advice: 'Slightly alkaline soil reduces iron, manganese and zinc availability. Apply gypsum (calcium sulphate) or elemental sulfur at 500 kg/ha. Use acidifying fertilizers like ammonium sulphate instead of urea.' }
  return { status: 'Very Alkaline', color: '#ef4444', advice: 'PROBLEM: Highly alkaline soil severely restricts most nutrient uptake. Apply elemental sulfur at 1-2 tonnes/ha and repeat annually. Iron chlorosis (yellowing) will be visible. Drip-apply chelated micronutrients.' }
}

function rainfallInsight(r) {
  if (r < 20) return { status: 'Dry', color: '#ef4444', advice: 'Very little rainfall. Irrigation is essential. Do not rely on natural rainfall. Monitor evapotranspiration — in hot weather, crops may need 40-60mm of water per week via irrigation.' }
  if (r < 60) return { status: 'Low', color: '#f59e0b', advice: 'Below-average rainfall. Supplement with irrigation. Prioritize moisture at critical crop stages — germination, flowering, and grain filling. Consider installing rainwater harvesting structures.' }
  if (r <= 150) return { status: 'Good', color: '#10b981', advice: 'Rainfall is adequate for most crops. You may be able to reduce irrigation frequency. Ensure proper field drainage to prevent waterlogging after heavy rain events.' }
  return { status: 'Excessive', color: '#38bdf8', advice: 'Very high rainfall. Ensure field drains are clear and functional. Excess water leads to nutrient leaching (especially N and K), root rot, and increased disease pressure. Postpone fertilizer application until fields drain.' }
}

const ZONE_LAYOUT = [
  { id: 'zone-1', label: 'Zone A', crop: '🌾', cropName: 'Rice Paddy', area: '4.5 Ac', soil: 'Clay Loam', x: 24, y: 24, width: 250, height: 180, fill: '#0d361c', stroke: '#22c55e', furrowDir: 'horizontal', probeX: 230, probeY: 165 },
  { id: 'zone-2', label: 'Zone B', crop: '🌽', cropName: 'Maize Field', area: '5.0 Ac', soil: 'Sandy Loam', x: 294, y: 24, width: 250, height: 180, fill: '#163e14', stroke: '#4ade80', furrowDir: 'vertical', probeX: 500, probeY: 165 },
  { id: 'zone-3', label: 'Zone C', crop: '☁️', cropName: 'Cotton Field', area: '4.0 Ac', soil: 'Black Soil', x: 564, y: 24, width: 252, height: 180, fill: '#133a25', stroke: '#86efac', furrowDir: 'horizontal', probeX: 770, probeY: 165 },
  { id: 'zone-4', label: 'Zone D', crop: '🌱', cropName: 'Soybean / Pulses', area: '5.2 Ac', soil: 'Red Loam', x: 24, y: 228, width: 386, height: 188, fill: '#0c3218', stroke: '#22c55e', furrowDir: 'horizontal', probeX: 365, probeY: 375 },
  { id: 'zone-5', label: 'Zone E', crop: '🍌', cropName: 'Banana Orchard', area: '4.8 Ac', soil: 'Alluvial', x: 430, y: 228, width: 386, height: 188, fill: '#082a14', stroke: '#4ade80', furrowDir: 'grid', probeX: 770, probeY: 375 },
]

function SensorPin({ zone, telemetry, isSelected, onClick }) {
  const moisture = telemetry?.soil_moisture ?? 55
  const mColor = moistureColor(moisture)
  const probeX = zone.probeX || (zone.x + zone.width - 45)
  const probeY = zone.probeY || (zone.y + zone.height - 40)

  // Furrow lines inside the rectangular field to give it a realistic cultivated field appearance
  const furrows = []
  if (zone.furrowDir === 'horizontal') {
    for (let py = zone.y + 42; py < zone.y + zone.height - 18; py += 18) {
      furrows.push(
        <line key={py} x1={zone.x + 10} y1={py} x2={zone.x + zone.width - 10} y2={py}
          stroke="rgba(255,255,255,0.08)" strokeWidth="1.5" strokeDasharray="6 4" />
      )
    }
  } else if (zone.furrowDir === 'vertical') {
    for (let px = zone.x + 28; px < zone.x + zone.width - 18; px += 20) {
      furrows.push(
        <line key={px} x1={px} y1={zone.y + 40} x2={px} y2={zone.y + zone.height - 12}
          stroke="rgba(255,255,255,0.08)" strokeWidth="1.5" strokeDasharray="6 4" />
      )
    }
  } else {
    for (let gx = zone.x + 36; gx < zone.x + zone.width - 24; gx += 38) {
      for (let gy = zone.y + 46; gy < zone.y + zone.height - 20; gy += 34) {
        furrows.push(
          <circle key={`${gx}-${gy}`} cx={gx} cy={gy} r="3" fill="rgba(74,222,128,0.2)" />
        )
      }
    }
  }

  return (
    <g style={{ cursor: 'pointer' }} onClick={onClick} role="button" aria-label={`Select ${zone.label}`}>
      {/* Square/Rectangular Field Plot */}
      <rect x={zone.x} y={zone.y} width={zone.width} height={zone.height} rx="8"
        fill={zone.fill}
        stroke={isSelected ? mColor : 'rgba(74,222,128,0.28)'}
        strokeWidth={isSelected ? 3.5 : 1.5}
        style={{
          transition: 'all 0.25s ease',
          filter: isSelected ? `drop-shadow(0 0 16px ${mColor}99)` : 'none',
        }}
      />

      {/* Internal Soil Cultivation Furrows */}
      {furrows}

      {/* Field Earthen Bund / Inner Rim */}
      <rect x={zone.x + 4} y={zone.y + 4} width={zone.width - 8} height={zone.height - 8} rx="6"
        fill="none" stroke="rgba(0,0,0,0.3)" strokeWidth="1" />

      {/* Selection Glow Tint */}
      {isSelected && (
        <rect x={zone.x} y={zone.y} width={zone.width} height={zone.height} rx="8"
          fill={mColor} opacity="0.08" />
      )}

      {/* Center Crop Watermark */}
      <text x={zone.x + zone.width / 2} y={zone.y + zone.height / 2 + 12}
        textAnchor="middle" fontSize={zone.width > 300 ? '46' : '36'} opacity="0.28">
        {zone.crop}
      </text>

      {/* Plot Name Tag (Top Left) */}
      <rect x={zone.x + 8} y={zone.y + 8} width={zone.width < 300 ? 155 : 190} height="24" rx="6"
        fill="#04140bE6" stroke={isSelected ? mColor : 'rgba(74,222,128,0.25)'} strokeWidth="1" />
      <text x={zone.x + 16} y={zone.y + 24}
        fill={isSelected ? '#f0fdf4' : '#86efac'}
        fontSize="11.5" fontWeight="700" fontFamily="Outfit,Inter,sans-serif">
        {zone.name || `${zone.crop} ${zone.label} · ${zone.cropName} (${zone.area})`}
      </text>

      {/* Active Inspection Tag (Top Right) */}
      {isSelected && (
        <g>
          <rect x={zone.x + zone.width - 92} y={zone.y + 8} width="84" height="20" rx="5"
            fill={mColor} opacity="0.9" />
          <text x={zone.x + zone.width - 50} y={zone.y + 22} textAnchor="middle"
            fill="#051a0e" fontSize="9.5" fontWeight="800" fontFamily="Outfit,Inter,sans-serif" letterSpacing="0.05em">
            ACTIVE PLOT
          </text>
        </g>
      )}

      {/* IoT Sensor Station Mast & Live Telemetry Marker */}
      <g>
        {/* Mast pole */}
        <line x1={probeX} y1={probeY} x2={probeX} y2={probeY - 26} stroke={mColor} strokeWidth="2" />
        {/* Solar panel */}
        <rect x={probeX - 8} y={probeY - 32} width="16" height="7" rx="2" fill="#0f172a" stroke={mColor} strokeWidth="1.2" />
        {/* Blinking signal wave when selected */}
        {isSelected && (
          <circle cx={probeX} cy={probeY - 28} r="10" fill="none" stroke={mColor} strokeWidth="1.8" opacity="0.6">
            <animate attributeName="r" from="6" to="22" dur="1.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" from="0.9" to="0" dur="1.5s" repeatCount="indefinite" />
          </circle>
        )}
        <circle cx={probeX} cy={probeY - 28} r="4.5" fill={mColor} stroke="#05140b" strokeWidth="1.5" />

        {/* Moisture Badge */}
        <rect x={probeX - 35} y={probeY - 2} width="70" height="22" rx="11"
          fill="#06180fEE" stroke={mColor} strokeWidth="1.4"
          filter="drop-shadow(0 2px 6px rgba(0,0,0,0.4))" />
        <text x={probeX} y={probeY + 13} textAnchor="middle" fill={mColor}
          fontSize="11" fontWeight="800" fontFamily="Outfit,Inter,sans-serif">
          💧 {moisture}%
        </text>
      </g>
    </g>
  )
}

function LiveDot() {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981',
        boxShadow: '0 0 8px #10b981', animation: 'livePulse 1.4s ease-in-out infinite', display: 'inline-block' }} />
      LIVE
    </span>
  )
}

// One insight card
function InsightCard({ icon, label, value, unit, insight }) {
  return (
    <div style={{
      background: 'linear-gradient(135deg,#0f2027 0%,#1a2e1a 100%)',
      border: `1px solid ${insight.color}33`,
      borderLeft: `4px solid ${insight.color}`,
      borderRadius: '12px', padding: '1.1rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.6rem' }}>
        <div>
          <div style={{ fontSize: '0.68rem', color: '#64748b', marginBottom: '0.1rem' }}>{icon} {label}</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: insight.color, lineHeight: 1 }}>
            {value}<span style={{ fontSize: '0.7rem', fontWeight: 500, color: '#475569', marginLeft: 2 }}>{unit}</span>
          </div>
        </div>
        <span style={{
          padding: '0.2rem 0.6rem', borderRadius: '20px', fontSize: '0.68rem', fontWeight: 700,
          background: `${insight.color}20`, color: insight.color, border: `1px solid ${insight.color}44`,
          whiteSpace: 'nowrap',
        }}>{insight.status}</span>
      </div>
      <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.55 }}>{insight.advice}</p>
    </div>
  )
}

export default function FarmDashboard() {
  const [zones, setZones] = useState([])
  const [randomTelemetry, setRandomTelemetry] = useState({})
  const [selectedZoneId, setSelectedZoneId] = useState('zone-1')
  const [zoneAdvisory, setZoneAdvisory] = useState(null)
  const [weather, setWeather] = useState(null)
  const [advisoryLoading, setAdvisoryLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState('')
  const [error, setError] = useState('')
  const [insightTab, setInsightTab] = useState('soil')

  useEffect(() => {
    const init = {}
    ZONE_LAYOUT.forEach(z => { init[z.id] = generateRandomTelemetry() })
    setRandomTelemetry(init)
    const iv = setInterval(() => {
      setRandomTelemetry(prev => {
        const next = { ...prev }
        ZONE_LAYOUT.forEach(z => {
          const old = prev[z.id] || {}
          next[z.id] = {
            N: Math.max(30, Math.min(150, (old.N || 80) + rnd(-5, 5, 0))),
            P: Math.max(10, Math.min(110, (old.P || 50) + rnd(-4, 4, 0))),
            K: Math.max(20, Math.min(130, (old.K || 60) + rnd(-4, 4, 0))),
            temperature: parseFloat(Math.max(15, Math.min(42, (old.temperature || 28) + rnd(-0.8, 0.8, 1))).toFixed(1)),
            humidity: Math.max(30, Math.min(95, (old.humidity || 60) + rnd(-3, 3, 0))),
            ph: parseFloat(Math.max(5.0, Math.min(8.5, (old.ph || 6.8) + rnd(-0.1, 0.1, 1))).toFixed(1)),
            rainfall: parseFloat(Math.max(0, Math.min(250, (old.rainfall || 100) + rnd(-5, 5, 1))).toFixed(1)),
            soil_moisture: Math.max(10, Math.min(95, (old.soil_moisture || 55) + rnd(-3, 3, 0))),
          }
        })
        return next
      })
    }, 4000)
    return () => clearInterval(iv)
  }, [])

  const fetchZones = async () => { try { const d = await farmApi.zones(); setZones(d) } catch {} }
  const fetchWeather = async () => { try { const w = await farmApi.weather(); setWeather(w) } catch {} }
  const fetchAdvisory = async (zoneId) => {
    setAdvisoryLoading(true)
    try { const a = await farmApi.advisory(zoneId); setZoneAdvisory(a) } catch {}
    finally { setAdvisoryLoading(false) }
  }
  useEffect(() => { fetchZones(); fetchWeather(); fetchAdvisory('zone-1') }, [])

  const handleSelectZone = (zoneId) => {
    setSelectedZoneId(zoneId); fetchAdvisory(zoneId); setActionMessage('')
  }

  const handleSimulate = async (scenario) => {
    setLoading(true)
    try {
      await farmApi.simulate(selectedZoneId, scenario)
      await fetchZones(); await fetchAdvisory(selectedZoneId)
      const labels = {
        dry_spell: '☀️ Dry spell simulated', monsoon_rain: '🌧️ Monsoon rain simulated',
        nutrient_depletion: '📉 NPK drawdown simulated', normal: '🔄 Normal drift simulated',
      }
      setActionMessage(labels[scenario] || 'Sensors updated.')
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const activeZoneData = ZONE_LAYOUT.map(layout => {
    const api = zones.find(z => z.id === layout.id) || {}
    return { ...layout, ...api, telemetry: randomTelemetry[layout.id] || {} }
  })

  const selectedZone = activeZoneData.find(z => z.id === selectedZoneId) || activeZoneData[0]
  const tele = selectedZone?.telemetry || {}
  const irrigation = zoneAdvisory?.journey_guidance?.irrigation || selectedZone?.irrigation_summary
  const mColor = moistureColor(tele.soil_moisture ?? 55)
  const weatherDisplay = weather || { temperature_c: 28.4, humidity_pct: 62, precipitation_mm: 3.2, wind_speed_kmh: 14 }

  // Compute all insights
  const insights = {
    N: nitrogenInsight(tele.N ?? 80),
    P: phosphorusInsight(tele.P ?? 50),
    K: potassiumInsight(tele.K ?? 60),
    moisture: moistureInsight(tele.soil_moisture ?? 55),
    temperature: temperatureInsight(tele.temperature ?? 28),
    humidity: humidityInsight(tele.humidity ?? 60),
    ph: phInsight(tele.ph ?? 6.8),
    rainfall: rainfallInsight(tele.rainfall ?? 80),
  }

  // Count alerts
  const alertCount = Object.values(insights).filter(i => i.status.toLowerCase().includes('low') || i.status.toLowerCase().includes('critical') || i.status.toLowerCase().includes('excess') || i.status.toLowerCase().includes('danger') || i.status.toLowerCase().includes('dry') || i.status.toLowerCase().includes('acidic') || i.status.toLowerCase().includes('alkaline') || i.status.toLowerCase().includes('hot') || i.status.toLowerCase().includes('waterlogged')).length

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');
        @keyframes livePulse { 0%,100%{opacity:1;box-shadow:0 0 8px #10b981} 50%{opacity:0.4;box-shadow:0 0 20px #10b981} }
        @keyframes slideUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
        @keyframes borderGlow { 0%,100%{box-shadow:0 0 12px rgba(16,185,129,0.25)} 50%{box-shadow:0 0 28px rgba(16,185,129,0.55)} }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
        .fd-wrap { font-family:'Outfit','Inter',sans-serif; max-width:1300px; margin:0 auto 3rem; background:linear-gradient(180deg,#06150b 0%,#091d11 100%); border-radius:24px; padding:1.8rem; border:1px solid rgba(74,222,128,0.18); box-shadow:0 25px 60px rgba(0,0,0,0.35),0 0 40px rgba(16,185,129,0.08); }
        .fd-wrap * { box-sizing:border-box; }
        .zone-pill { cursor:pointer; padding:0.45rem 1.15rem; border-radius:30px; font-size:0.82rem; font-weight:700; border:1.5px solid rgba(74,222,128,0.25); background:rgba(16,185,129,0.08); color:#cbd5e1; transition:all 0.2s; font-family:inherit; }
        .zone-pill:hover { background:rgba(16,185,129,0.22); border-color:#10b981; color:#86efac; }
        .zone-pill.active { background:linear-gradient(135deg,rgba(16,185,129,0.35) 0%,rgba(5,150,105,0.25) 100%); border-color:#10b981; color:#ecfdf5; box-shadow:0 0 16px rgba(16,185,129,0.4); }
        .sc { background:linear-gradient(145deg,#0d2718 0%,#081b11 100%); border:1px solid rgba(74,222,128,0.18); border-radius:12px; padding:0.85rem; animation:slideUp 0.3s ease; box-shadow:0 4px 12px rgba(0,0,0,0.25); }
        .sim-btn { cursor:pointer; padding:0.55rem 0.8rem; border-radius:8px; font-size:0.8rem; font-weight:700; border:1px solid rgba(56,189,248,0.3); background:rgba(15,23,42,0.8); color:#e2e8f0; transition:all 0.2s; font-family:inherit; }
        .sim-btn:hover:not(:disabled) { background:rgba(56,189,248,0.22); border-color:#38bdf8; color:#7dd3fc; box-shadow:0 0 12px rgba(56,189,248,0.3); }
        .sim-btn:disabled { opacity:0.5; cursor:default; }
        .adv-card { background:linear-gradient(135deg,#0d2618 0%,#091a10 100%); border-radius:14px; padding:1.3rem; border:1px solid rgba(74,222,128,0.2); animation:slideUp 0.4s ease; box-shadow:0 6px 18px rgba(0,0,0,0.25); }
        .itab { cursor:pointer; padding:0.45rem 1.1rem; border-radius:8px; font-size:0.8rem; font-weight:700; border:1px solid transparent; background:transparent; color:#94a3b8; transition:all 0.2s; font-family:inherit; }
        .itab:hover { color:#e2e8f0; background:rgba(255,255,255,0.06); }
        .itab.on { background:rgba(16,185,129,0.22); border-color:#10b981; color:#86efac; box-shadow:0 0 10px rgba(16,185,129,0.25); }
      `}</style>

      <div className="fd-wrap">

        {/* ═══ HEADER ═══ */}
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:'1rem',
          padding:'1.2rem 1.8rem', background:'linear-gradient(135deg,#0a1f0a 0%,#0f2d1e 100%)',
          borderRadius:'16px', border:'1px solid rgba(16,185,129,0.25)', marginBottom:'1.4rem',
          animation:'borderGlow 3s ease-in-out infinite' }}>
          <div>
            <div style={{ display:'flex', alignItems:'center', gap:'0.65rem', marginBottom:'0.3rem' }}>
              <span style={{ background:'rgba(16,185,129,0.18)', border:'1px solid #10b981', padding:'0.22rem 0.7rem',
                borderRadius:'20px', fontSize:'0.7rem', fontWeight:700, color:'#10b981', letterSpacing:'0.08em' }}>
                🌾 SMART FARM COMMAND CENTER
              </span>
              <span style={{ fontSize:'0.72rem', color:'#10b981', fontWeight:700 }}><LiveDot /></span>
              {alertCount > 0 && (
                <span style={{ background:'rgba(239,68,68,0.2)', border:'1px solid #ef4444', padding:'0.18rem 0.6rem',
                  borderRadius:'20px', fontSize:'0.7rem', fontWeight:700, color:'#ef4444',
                  animation:'pulse 1.5s ease-in-out infinite' }}>
                  ⚠️ {alertCount} Alert{alertCount > 1 ? 's' : ''} Detected
                </span>
              )}
            </div>
            <h2 style={{ margin:0, fontSize:'1.55rem', fontWeight:800, color:'#f0fdf4', letterSpacing:'-0.02em' }}>
              Precision Agriculture · 5-Zone IoT Field Monitor
            </h2>
            <p style={{ margin:'0.2rem 0 0', fontSize:'0.85rem', color:'#86efac', opacity:0.85 }}>
              Real-time soil sensors · Auto irrigation · AI agronomy · MLOps-powered decisions
            </p>
          </div>
          <div style={{ display:'flex', gap:'1.4rem', flexWrap:'wrap', background:'rgba(0,0,0,0.25)',
            padding:'0.85rem 1.3rem', borderRadius:'12px', border:'1px solid rgba(255,255,255,0.07)' }}>
            {[
              { label:'TEMP', value:`${weatherDisplay.temperature_c}°C`, icon:'🌡️' },
              { label:'HUMIDITY', value:`${weatherDisplay.humidity_pct}%`, icon:'💧' },
              { label:'PRECIP', value:`${weatherDisplay.precipitation_mm} mm`, icon:'🌧️' },
              { label:'WIND', value:`${weatherDisplay.wind_speed_kmh} km/h`, icon:'💨' },
            ].map(w => (
              <div key={w.label} style={{ textAlign:'center' }}>
                <div style={{ fontSize:'0.68rem', color:'#64748b', marginBottom:'0.1rem' }}>{w.icon} {w.label}</div>
                <div style={{ fontSize:'1rem', fontWeight:700, color:'#f0fdf4' }}>{w.value}</div>
              </div>
            ))}
          </div>
        </div>

        {actionMessage && <div style={{ marginBottom:'1rem', padding:'0.65rem 1.2rem', background:'rgba(16,185,129,0.1)', border:'1px solid #10b981', borderRadius:'8px', color:'#4ade80', fontSize:'0.86rem' }}>✓ {actionMessage}</div>}
        {error && <div style={{ marginBottom:'1rem', padding:'0.65rem 1.2rem', background:'rgba(239,68,68,0.1)', border:'1px solid #ef4444', borderRadius:'8px', color:'#fca5a5', fontSize:'0.86rem' }}>⚠ {error}</div>}

        {/* ZONE PILLS */}
        <div style={{ display:'flex', gap:'0.5rem', flexWrap:'wrap', marginBottom:'1.1rem', alignItems:'center' }}>
          <span style={{ fontSize:'0.72rem', color:'#64748b', fontWeight:700, marginRight:'0.4rem' }}>SELECT ZONE:</span>
          {activeZoneData.map(z => (
            <button key={z.id} className={`zone-pill ${z.id === selectedZoneId ? 'active' : ''}`} onClick={() => handleSelectZone(z.id)}>
              {z.crop} {z.label}
            </button>
          ))}
        </div>

        {/* ═══ MAIN GRID: MAP + SENSORS ═══ */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 370px', gap:'1.4rem', alignItems:'start' }}>

          {/* FARM MAP */}
          <div style={{ background:'linear-gradient(180deg,#0a1f0a 0%,#052e16 40%,#071a0e 100%)',
            borderRadius:'18px', border:'1px solid rgba(74,222,128,0.2)', padding:'1.4rem 1.4rem 0.9rem' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'0.9rem' }}>
              <div>
                <div style={{ fontSize:'0.7rem', color:'#4ade80', fontWeight:700, letterSpacing:'0.08em' }}>🗺 FIELD AERIAL VIEW</div>
                <div style={{ fontSize:'1.05rem', fontWeight:700, color:'#f0fdf4', marginTop:'0.1rem' }}>Kaushal Agri Estate — 23.5 Acres</div>
              </div>
              <span style={{ fontSize:'0.72rem', color:'#10b981', fontWeight:700 }}><LiveDot /> Sensors Active</span>
            </div>
            <div style={{ borderRadius:'12px', overflow:'hidden', border:'1px solid rgba(74,222,128,0.2)' }}>
              <svg viewBox="0 0 840 440" width="100%" style={{ display:'block', background:'#06180e' }}>
                {/* Farm Base Turf */}
                <rect x="0" y="0" width="840" height="440" fill="#06180e" />

                {/* Earthen Access Roads separating the square field plots */}
                {/* Horizontal Central Road */}
                <rect x="20" y="206" width="800" height="20" fill="#152618" rx="2" />
                <line x1="24" y1="216" x2="816" y2="216" stroke="#253d25" strokeWidth="1.5" strokeDasharray="8 6" />

                {/* Vertical Road between Plot A and Plot B */}
                <rect x="274" y="24" width="20" height="182" fill="#152618" rx="2" />
                <line x1="284" y1="28" x2="284" y2="202" stroke="#253d25" strokeWidth="1.5" strokeDasharray="8 6" />

                {/* Vertical Road between Plot B and Plot C */}
                <rect x="544" y="24" width="20" height="182" fill="#152618" rx="2" />
                <line x1="554" y1="28" x2="554" y2="202" stroke="#253d25" strokeWidth="1.5" strokeDasharray="8 6" />

                {/* Vertical Road between Plot D and Plot E */}
                <rect x="410" y="228" width="20" height="188" fill="#152618" rx="2" />
                <line x1="420" y1="232" x2="420" y2="412" stroke="#253d25" strokeWidth="1.5" strokeDasharray="8 6" />

                {/* Main Irrigation Canal running through central corridor */}
                <path d="M 24 216 L 816 216" stroke="#0284c7" strokeWidth="6" strokeLinecap="round" opacity="0.8" />
                <path d="M 24 216 L 816 216" stroke="#38bdf8" strokeWidth="2.5" strokeDasharray="14 10" strokeLinecap="round">
                  <animate attributeName="stroke-dashoffset" from="0" to="-48" dur="2s" repeatCount="indefinite" />
                </path>
                <text x="32" y="213" fill="#38bdf8" fontSize="8.5" fontWeight="700" fontFamily="Outfit,Inter,sans-serif" letterSpacing="0.08em">
                  ══ MAIN IRRIGATION CANAL ══
                </text>

                {/* Outer Estate Perimeter Fence */}
                <rect x="14" y="14" width="812" height="412" rx="12" fill="none" stroke="rgba(74,222,128,0.25)" strokeWidth="1.5" strokeDasharray="8 5" />

                {/* 5 Square/Rectangular Field Plots */}
                {activeZoneData.map(zone => (
                  <SensorPin key={zone.id} zone={zone} telemetry={zone.telemetry}
                    isSelected={zone.id === selectedZoneId} onClick={() => handleSelectZone(zone.id)} />
                ))}

                {/* Compass Rose */}
                <g transform="translate(806, 38)">
                  <circle cx="0" cy="0" r="14" fill="#04120aCC" stroke="rgba(74,222,128,0.3)" strokeWidth="1" />
                  <text x="0" y="-3" textAnchor="middle" fill="#4ade80" fontSize="9" fontWeight="800" fontFamily="Outfit,sans-serif">N</text>
                  <polygon points="0,-11 -3,-2 3,-2" fill="#ef4444" />
                  <polygon points="0,11 -3,2 3,2" fill="#94a3b8" />
                </g>
              </svg>
            </div>
            <div style={{ display:'flex', gap:'1.2rem', marginTop:'0.8rem', flexWrap:'wrap', alignItems:'center' }}>
              {[
                { color:'#ef4444', label:'Critical (<30%)' },
                { color:'#f59e0b', label:'Low (30-50%)' },
                { color:'#10b981', label:'Optimal (50-75%)' },
                { color:'#38bdf8', label:'Saturated (>75%)' },
              ].map(l => (
                <div key={l.label} style={{ display:'flex', alignItems:'center', gap:'0.4rem', fontSize:'0.73rem', color:'#64748b' }}>
                  <span style={{ width:9, height:9, borderRadius:'50%', background:l.color, display:'inline-block', boxShadow:`0 0 6px ${l.color}88` }} />
                  {l.label}
                </div>
              ))}
              <div style={{ fontSize:'0.7rem', color:'#334155', marginLeft:'auto' }}>💡 Click any zone to inspect</div>
            </div>
          </div>

          {/* RIGHT PANEL */}
          <div style={{ display:'flex', flexDirection:'column', gap:'0.9rem' }}>
            {/* Zone header */}
            <div style={{ background:'linear-gradient(135deg,#0a1f0a,#0f2d1e)', borderRadius:'14px', border:`1.5px solid ${mColor}55`, padding:'1rem 1.2rem' }}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <div>
                  <div style={{ fontSize:'0.68rem', color:'#4ade80', fontWeight:700, letterSpacing:'0.08em' }}>ACTIVE ZONE</div>
                  <div style={{ fontSize:'1.25rem', fontWeight:800, color:'#f0fdf4' }}>{selectedZone?.name || `${selectedZone?.label} · ${selectedZone?.active_crop || 'Rice'}`}</div>
                  <div style={{ fontSize:'0.78rem', color:'#64748b', marginTop:'0.1rem' }}>{selectedZone?.area_acres || '4'} Acres · {selectedZone?.soil_type || 'Loamy'}</div>
                </div>
                <div style={{ width:54, height:54, borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center',
                  background:`conic-gradient(${mColor} ${(tele.soil_moisture ?? 55) * 3.6}deg, rgba(255,255,255,0.05) 0)`,
                  border:`2px solid ${mColor}`, boxShadow:`0 0 18px ${mColor}66` }}>
                  <span style={{ fontSize:'0.62rem', fontWeight:800, color:'#f0fdf4' }}>{tele.soil_moisture ?? 55}%</span>
                </div>
              </div>
            </div>

            {/* 8 Sensor Cards */}
            <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:'0.55rem' }}>
              {[
                { icon:'🌱', label:'Nitrogen (N)', value:tele.N, unit:'kg/ha', color:'#4ade80' },
                { icon:'🧪', label:'Phosphorus (P)', value:tele.P, unit:'kg/ha', color:'#a78bfa' },
                { icon:'💎', label:'Potassium (K)', value:tele.K, unit:'kg/ha', color:'#fbbf24' },
                { icon:'🌊', label:'Soil Moisture', value:tele.soil_moisture, unit:'%', color:mColor },
                { icon:'🌡️', label:'Temperature', value:fmt(tele.temperature,1), unit:'°C', color:'#f87171' },
                { icon:'💧', label:'Humidity', value:tele.humidity, unit:'%', color:'#38bdf8' },
                { icon:'⚖️', label:'Soil pH', value:fmt(tele.ph,1), unit:'', color:'#fb923c' },
                { icon:'🌧️', label:'Rainfall', value:fmt(tele.rainfall,1), unit:'mm', color:'#60a5fa' },
              ].map(s => (
                <div key={s.label} className="sc">
                  <div style={{ fontSize:'0.68rem', color:'#64748b', marginBottom:'0.18rem' }}>{s.icon} {s.label}</div>
                  <div style={{ fontSize:'1.3rem', fontWeight:800, color:s.color, lineHeight:1 }}>
                    {s.value}<span style={{ fontSize:'0.62rem', fontWeight:500, color:'#475569', marginLeft:2 }}>{s.unit}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Irrigation */}
            {irrigation && (
              <div style={{ borderRadius:'14px', padding:'1rem 1.2rem',
                background:`linear-gradient(145deg, ${irrigation.status_color||'#10b981'}22 0%, #06170d 100%)`,
                border:`1.5px solid ${irrigation.status_color||'#10b981'}66`,
                boxShadow:`0 4px 16px ${irrigation.status_color||'#10b981'}25` }}>
                <div style={{ fontSize:'0.7rem', fontWeight:800, color:irrigation.status_color||'#10b981', letterSpacing:'0.08em', marginBottom:'0.25rem' }}>SMART IRRIGATION CONTROLLER</div>
                <div style={{ fontSize:'1rem', fontWeight:800, color:'#f0fdf4', marginBottom:'0.55rem' }}>
                  {irrigation.status==='CRITICAL_DEFICIT'?'🚨 Critical Water Deficit':
                   irrigation.status==='MODERATE_DEFICIT'?'⚠️ Moderate Irrigation Needed':
                   irrigation.status==='WATERLOGGED'?'🌊 Drainage Required':'✅ Optimal Soil Moisture'}
                </div>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:'0.55rem' }}>
                  {[
                    { l:'Deficit', v:irrigation.moisture_deficit_pct>0?`-${irrigation.moisture_deficit_pct}%`:'None' },
                    { l:'Water Vol', v:irrigation.water_volume_liters?`${irrigation.water_volume_liters?.toLocaleString()} L`:'0 L' },
                    { l:'Pump Runtime', v:irrigation.estimated_pump_runtime_hours?`${irrigation.estimated_pump_runtime_hours} hrs`:'Off' },
                    { l:'Method', v:irrigation.recommended_method||'Drip' },
                  ].map(x => (
                    <div key={x.l} style={{ background:'rgba(0,0,0,0.3)', padding:'0.45rem 0.6rem', borderRadius:'8px', border:'1px solid rgba(255,255,255,0.06)' }}>
                      <div style={{ fontSize:'0.65rem', color:'#94a3b8', fontWeight:600 }}>{x.l}</div>
                      <div style={{ fontSize:'0.9rem', fontWeight:800, color:'#f0fdf4' }}>{x.v}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Simulation */}
            <div style={{ background:'linear-gradient(145deg, #0d2718 0%, #081b11 100%)', borderRadius:'14px', border:'1px solid rgba(74,222,128,0.18)', padding:'1rem', boxShadow:'0 4px 12px rgba(0,0,0,0.25)' }}>
              <div style={{ fontSize:'0.7rem', fontWeight:800, color:'#4ade80', letterSpacing:'0.08em', marginBottom:'0.65rem' }}>🔬 SENSOR SCENARIO SIMULATOR</div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:'0.5rem' }}>
                {[
                  { key:'dry_spell', label:'☀️ Dry Spell' },
                  { key:'monsoon_rain', label:'🌧️ Monsoon' },
                  { key:'nutrient_depletion', label:'📉 NPK Depletion' },
                  { key:'normal', label:'🔄 Normal Shift' },
                ].map(s => (
                  <button key={s.key} className="sim-btn" onClick={() => handleSimulate(s.key)} disabled={loading}>{s.label}</button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ═══ FARMER ADVISORY & INSIGHTS ═══ */}
        <div style={{ marginTop:'2rem' }}>
          {/* Section header */}
          <div style={{
            display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:'1rem',
            padding:'1rem 1.4rem',
            background:'linear-gradient(135deg,#0f1e2e 0%,#0a1f12 100%)',
            borderRadius:'14px', border:'1px solid rgba(16,185,129,0.2)', marginBottom:'1.2rem',
          }}>
            <div>
              <div style={{ fontSize:'0.7rem', color:'#4ade80', fontWeight:700, letterSpacing:'0.08em', marginBottom:'0.2rem' }}>
                🧑‍🌾 FARMER ADVISORY DASHBOARD
              </div>
              <div style={{ fontSize:'1.15rem', fontWeight:800, color:'#f0fdf4' }}>
                {selectedZone?.label} — Complete Field Health Report & Action Guide
              </div>
              <div style={{ fontSize:'0.82rem', color:'#86efac', opacity:0.8, marginTop:'0.1rem' }}>
                Every reading explained in plain language with specific actions you should take today
              </div>
            </div>
            <div style={{ display:'flex', gap:'0.4rem', flexWrap:'wrap' }}>
              {[
                { id:'soil', label:'🌱 Soil Nutrients' },
                { id:'water', label:'💧 Water & Climate' },
                { id:'summary', label:'📋 Action Summary' },
              ].map(t => (
                <button key={t.id} className={`itab ${insightTab===t.id?'on':''}`} onClick={() => setInsightTab(t.id)}>{t.label}</button>
              ))}
            </div>
          </div>

          {/* TAB: Soil Nutrients */}
          {insightTab === 'soil' && (
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(300px,1fr))', gap:'1rem', animation:'slideUp 0.3s ease' }}>
              <InsightCard icon="🌱" label="Nitrogen (N)" value={tele.N} unit="kg/ha" insight={insights.N} />
              <InsightCard icon="🧪" label="Phosphorus (P)" value={tele.P} unit="kg/ha" insight={insights.P} />
              <InsightCard icon="💎" label="Potassium (K)" value={tele.K} unit="kg/ha" insight={insights.K} />
              <InsightCard icon="⚖️" label="Soil pH" value={fmt(tele.ph,1)} unit="" insight={insights.ph} />
            </div>
          )}

          {/* TAB: Water & Climate */}
          {insightTab === 'water' && (
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(300px,1fr))', gap:'1rem', animation:'slideUp 0.3s ease' }}>
              <InsightCard icon="🌊" label="Soil Moisture" value={`${tele.soil_moisture}%`} unit="" insight={insights.moisture} />
              <InsightCard icon="🌧️" label="Rainfall" value={fmt(tele.rainfall,1)} unit="mm" insight={insights.rainfall} />
              <InsightCard icon="🌡️" label="Temperature" value={fmt(tele.temperature,1)} unit="°C" insight={insights.temperature} />
              <InsightCard icon="💧" label="Relative Humidity" value={`${tele.humidity}%`} unit="" insight={insights.humidity} />
            </div>
          )}

          {/* TAB: Action Summary */}
          {insightTab === 'summary' && (
            <div style={{ animation:'slideUp 0.3s ease' }}>
              {/* Priority action banner */}
              <div style={{ background:'linear-gradient(135deg,#1a0f0f,#1a150a)', border:'1px solid #f59e0b44',
                borderRadius:'14px', padding:'1.2rem 1.4rem', marginBottom:'1rem' }}>
                <div style={{ fontSize:'0.7rem', color:'#fbbf24', fontWeight:700, letterSpacing:'0.07em', marginBottom:'0.5rem' }}>
                  📋 TODAY'S PRIORITY ACTION LIST — {selectedZone?.label}
                </div>
                <div style={{ display:'flex', flexDirection:'column', gap:'0.6rem' }}>
                  {Object.entries(insights).map(([key, ins], idx) => {
                    const labels = { N:'Nitrogen', P:'Phosphorus', K:'Potassium', moisture:'Soil Moisture', temperature:'Temperature', humidity:'Humidity', ph:'Soil pH', rainfall:'Rainfall' }
                    const isAction = ins.status !== 'Optimal' && ins.status !== 'Good' && ins.status !== 'Cool'
                    if (!isAction) return null
                    return (
                      <div key={key} style={{ display:'flex', gap:'1rem', alignItems:'flex-start',
                        padding:'0.75rem 1rem', background:'rgba(255,255,255,0.03)', borderRadius:'10px',
                        borderLeft:`3px solid ${ins.color}` }}>
                        <span style={{ background:`${ins.color}22`, color:ins.color, border:`1px solid ${ins.color}44`,
                          padding:'0.2rem 0.5rem', borderRadius:'6px', fontSize:'0.68rem', fontWeight:700, minWidth:80, textAlign:'center' }}>
                          {ins.status}
                        </span>
                        <div>
                          <div style={{ fontSize:'0.82rem', fontWeight:700, color:'#e2e8f0', marginBottom:'0.2rem' }}>{labels[key]}</div>
                          <div style={{ fontSize:'0.78rem', color:'#94a3b8', lineHeight:1.5 }}>{ins.advice}</div>
                        </div>
                      </div>
                    )
                  })}
                  {Object.values(insights).every(i => i.status === 'Optimal' || i.status === 'Good' || i.status === 'Cool') && (
                    <div style={{ textAlign:'center', padding:'2rem', color:'#10b981' }}>
                      <div style={{ fontSize:'2rem' }}>✅</div>
                      <div style={{ fontWeight:700, marginTop:'0.5rem' }}>All systems optimal! No urgent actions needed today.</div>
                      <div style={{ fontSize:'0.82rem', color:'#64748b', marginTop:'0.3rem' }}>Continue regular monitoring every 24-48 hours.</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Optimal readings */}
              <div style={{ background:'rgba(16,185,129,0.06)', border:'1px solid rgba(16,185,129,0.2)',
                borderRadius:'14px', padding:'1.2rem 1.4rem' }}>
                <div style={{ fontSize:'0.7rem', color:'#10b981', fontWeight:700, letterSpacing:'0.07em', marginBottom:'0.6rem' }}>
                  ✅ READINGS IN OPTIMAL RANGE — No Action Required
                </div>
                <div style={{ display:'flex', flexWrap:'wrap', gap:'0.5rem' }}>
                  {Object.entries(insights).map(([key, ins]) => {
                    const labels = { N:'N', P:'P', K:'K', moisture:'Moisture', temperature:'Temp', humidity:'Humidity', ph:'pH', rainfall:'Rainfall' }
                    if (ins.status !== 'Optimal' && ins.status !== 'Good' && ins.status !== 'Cool') return null
                    return (
                      <span key={key} style={{ padding:'0.3rem 0.8rem', borderRadius:'20px', fontSize:'0.8rem', fontWeight:600,
                        background:'rgba(16,185,129,0.15)', border:'1px solid #10b98144', color:'#4ade80' }}>
                        ✓ {labels[key]}
                      </span>
                    )
                  })}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ═══ AI AGRONOMY ADVISORY ═══ */}
        {(zoneAdvisory || advisoryLoading) && (
          <div style={{ marginTop:'1.8rem' }}>
            <div style={{ display:'flex', alignItems:'center', gap:'0.65rem', marginBottom:'0.9rem' }}>
              <div style={{ fontSize:'0.7rem', color:'#4ade80', fontWeight:700, letterSpacing:'0.08em' }}>🤖 AI AGRONOMY ENGINE</div>
              {advisoryLoading && <span style={{ fontSize:'0.78rem', color:'#38bdf8' }}>Analyzing field data…</span>}
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))', gap:'1rem' }}>
              <div className="adv-card">
                <div style={{ fontSize:'0.68rem', color:'#4ade80', fontWeight:700, letterSpacing:'0.07em', marginBottom:'0.55rem' }}>🌱 CROP SUITABILITY RANKING</div>
                <p style={{ fontSize:'0.78rem', color:'#64748b', margin:'0 0 0.6rem' }}>Based on your current soil NPK, pH, moisture and temperature, our AI model ranks which crops will perform best in this zone right now:</p>
                <div style={{ display:'flex', flexWrap:'wrap', gap:'0.5rem' }}>
                  {zoneAdvisory?.journey_guidance?.crop_suitability?.ranked_alternatives?.map((item, idx) => (
                    <span key={idx} style={{ padding:'0.3rem 0.8rem', borderRadius:'20px', fontSize:'0.8rem', fontWeight:700,
                      background:idx===0?'rgba(16,185,129,0.2)':'rgba(255,255,255,0.05)',
                      border:idx===0?'1px solid #10b981':'1px solid rgba(255,255,255,0.08)',
                      color:idx===0?'#10b981':'#94a3b8' }}>
                      #{idx+1} {item.crop} · {((item.probability||item.confidence||0.8)*100).toFixed(0)}%
                    </span>
                  )) || <span style={{ color:'#64748b', fontSize:'0.82rem' }}>Loading…</span>}
                </div>
              </div>

              {zoneAdvisory?.journey_guidance?.fertilizer && (
                <div className="adv-card">
                  <div style={{ fontSize:'0.68rem', color:'#fbbf24', fontWeight:700, letterSpacing:'0.07em', marginBottom:'0.55rem' }}>🧪 FERTILIZER PRESCRIPTION</div>
                  <p style={{ fontSize:'0.78rem', color:'#64748b', margin:'0 0 0.5rem' }}>Based on your soil nutrient deficiency analysis:</p>
                  <div style={{ fontSize:'0.88rem', color:'#e2e8f0', lineHeight:1.5 }}>
                    {zoneAdvisory.journey_guidance.fertilizer.fertilizer_name
                      ? <><strong style={{ color:'#fbbf24' }}>{zoneAdvisory.journey_guidance.fertilizer.fertilizer_name}</strong>
                          <span style={{ color:'#94a3b8' }}> — {zoneAdvisory.journey_guidance.fertilizer.estimated_bags_50kg} × 50kg bags for {selectedZone.area_acres || 4} acres.</span>
                          <p style={{ fontSize:'0.78rem', color:'#64748b', marginTop:'0.4rem', marginBottom:0 }}>Apply in split doses: 50% at transplanting, 25% at tillering, 25% at panicle initiation. Always apply in moist soil, never dry.</p></>
                      : 'N-P-K levels are within maintenance limits. No additional fertilizer needed this week.'}
                  </div>
                </div>
              )}

              {zoneAdvisory?.journey_guidance?.pest_protection && (
                <div className="adv-card">
                  <div style={{ fontSize:'0.68rem', color:'#f87171', fontWeight:700, letterSpacing:'0.07em', marginBottom:'0.55rem' }}>🐛 PEST PROTECTION ALERT</div>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'0.5rem' }}>
                    <span style={{ fontSize:'0.92rem', fontWeight:700, color:'#e2e8f0' }}>{zoneAdvisory.journey_guidance.pest_protection.primary_pest}</span>
                    <span style={{ display:'inline-block', padding:'0.18rem 0.55rem', borderRadius:'20px', fontSize:'0.7rem', fontWeight:700,
                      background:'rgba(239,68,68,0.18)', color:'#f87171', border:'1px solid #ef444444' }}>
                      {zoneAdvisory.journey_guidance.pest_protection.risk_assessment?.risk_level||'Moderate'} Risk
                    </span>
                  </div>
                  <p style={{ fontSize:'0.78rem', color:'#64748b', margin:'0 0 0.4rem' }}>Current temperature and humidity conditions create a favorable environment for this pest. Inspect your crop every 2-3 days.</p>
                  <div style={{ fontSize:'0.82rem', color:'#94a3b8', lineHeight:1.5, padding:'0.6rem', background:'rgba(255,255,255,0.03)', borderRadius:'8px' }}>
                    🌿 <strong style={{ color:'#4ade80' }}>Organic remedy:</strong> {zoneAdvisory.journey_guidance.pest_protection.organic_control}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ═══ FARMER'S QUICK REFERENCE LEGEND ═══ */}
        <div style={{ marginTop:'1.8rem', background:'linear-gradient(135deg,#0f1e0f,#0a1418)', borderRadius:'16px', padding:'1.4rem', border:'1px solid rgba(255,255,255,0.07)' }}>
          <div style={{ fontSize:'0.7rem', color:'#4ade80', fontWeight:700, letterSpacing:'0.08em', marginBottom:'1rem' }}>
            📚 FARMER'S QUICK REFERENCE GUIDE — Understanding Your Sensor Numbers
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))', gap:'0.75rem' }}>
            {[
              { icon:'🌱', label:'Nitrogen (N)', good:'80–120 kg/ha', low:'<50 = Apply Urea', high:'>130 = Skip fertilizer', tip:'Controls leaf/stem growth & green color' },
              { icon:'🧪', label:'Phosphorus (P)', good:'40–80 kg/ha', low:'<25 = Apply DAP', high:'>90 = Stop P fertilizer', tip:'Drives root growth, flowering, seed formation' },
              { icon:'💎', label:'Potassium (K)', good:'60–100 kg/ha', low:'<35 = Apply MOP', high:'>120 = Skip potash', tip:'Strengthens stems, improves fruit quality' },
              { icon:'🌊', label:'Soil Moisture', good:'50–70%', low:'<30% = Irrigate NOW', high:'>80% = Open drains', tip:'Root zone water availability for crop uptake' },
              { icon:'🌡️', label:'Temperature', good:'20–32°C', low:'<15°C = Frost risk', high:'>38°C = Heat stress', tip:'Controls growth rate and nutrient absorption' },
              { icon:'⚖️', label:'Soil pH', good:'6.0–7.2', low:'<5.5 = Apply lime', high:'>8.0 = Apply sulfur', tip:'Controls nutrient availability to roots' },
              { icon:'💧', label:'Humidity', good:'50–70%', low:'<40% = Drought stress', high:'>85% = Fungal risk', tip:'Affects transpiration & disease pressure' },
              { icon:'🌧️', label:'Rainfall', good:'60–150 mm/week', low:'<20 = Irrigate', high:'>200 = Drainage needed', tip:'Replaces irrigation need partially/fully' },
            ].map(r => (
              <div key={r.label} style={{ padding:'0.9rem', background:'rgba(255,255,255,0.03)', borderRadius:'10px', border:'1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ fontSize:'0.82rem', fontWeight:700, color:'#e2e8f0', marginBottom:'0.4rem' }}>{r.icon} {r.label}</div>
                <div style={{ display:'flex', gap:'0.4rem', flexWrap:'wrap', marginBottom:'0.4rem' }}>
                  <span style={{ fontSize:'0.68rem', padding:'0.15rem 0.45rem', borderRadius:'6px', background:'rgba(16,185,129,0.15)', color:'#4ade80', border:'1px solid #10b98133' }}>✓ {r.good}</span>
                </div>
                <div style={{ fontSize:'0.7rem', color:'#ef4444', marginBottom:'0.15rem' }}>↓ {r.low}</div>
                <div style={{ fontSize:'0.7rem', color:'#38bdf8', marginBottom:'0.35rem' }}>↑ {r.high}</div>
                <div style={{ fontSize:'0.7rem', color:'#475569', fontStyle:'italic' }}>{r.tip}</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </>
  )
}
