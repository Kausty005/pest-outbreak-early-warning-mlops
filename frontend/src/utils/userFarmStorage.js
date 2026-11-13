/**
 * User-isolated farm storage and multi-tenant agricultural state management.
 * Ensures each farmer user has an independent estate, crops, and telemetry dashboard.
 */

export function sanitizeUserId(user) {
  if (!user) return 'default'
  const raw = user.id || user.email || user.name || 'default'
  return String(raw).trim().toLowerCase().replace(/[^a-z0-9]/g, '_')
}

export function getFarmStorageKeyForUser(user) {
  const sanitized = sanitizeUserId(user)
  return `agri_farm_profile_${sanitized}`
}

export const PRESET_FARMERS = [
  {
    id: 'farmer_kaushal_sharma',
    name: 'Kaushal Sharma',
    role: 'Farm Owner / Agronomist',
    state: 'Maharashtra',
    district: 'Nagpur',
    primaryCrop: 'Rice',
    avatar: '👨‍🌾',
    badgeColor: '#10B981',
    initialFarm: {
      estateName: "Kaushal's Vidarbha Agro-Estate",
      primaryCrop: 'Rice',
      state: 'Maharashtra',
      area: 12.5,
      zones: [
        { id: 'zone-1', label: 'Sector A', crop: 'Rice', cropName: 'Paddy Wetland', area: '4.5 Ac' },
        { id: 'zone-2', label: 'Sector B', crop: 'Soybean', cropName: 'Kharif Legume Plot', area: '4.0 Ac' },
        { id: 'zone-3', label: 'Sector C', crop: 'Cotton', cropName: 'Bt Cotton Field', area: '4.0 Ac' },
      ],
      timestamp: new Date().toISOString(),
    },
  },
  {
    id: 'farmer_ramesh_patel',
    name: 'Ramesh Patel',
    role: 'Commercial Cash Crop Grower',
    state: 'Gujarat',
    district: 'Rajkot',
    primaryCrop: 'Cotton',
    avatar: '🤠',
    badgeColor: '#F59E0B',
    initialFarm: {
      estateName: "Ramesh's Saurashtra Cotton Acres",
      primaryCrop: 'Cotton',
      state: 'Gujarat',
      area: 18.0,
      zones: [
        { id: 'zone-1', label: 'Sector 1', crop: 'Cotton', cropName: 'Hybrid Cotton Quad 1', area: '5.0 Ac' },
        { id: 'zone-2', label: 'Sector 2', crop: 'Cotton', cropName: 'Hybrid Cotton Quad 2', area: '5.0 Ac' },
        { id: 'zone-3', label: 'Sector 3', crop: 'Groundnut', cropName: 'Oilseed Semi-Arid Field', area: '4.0 Ac' },
        { id: 'zone-4', label: 'Sector 4', crop: 'Maize', cropName: 'Fodder Maize Boundary', area: '4.0 Ac' },
      ],
      timestamp: new Date().toISOString(),
    },
  },
  {
    id: 'farmer_gurpreet_singh',
    name: 'Gurpreet Singh',
    role: 'Grain Production Manager',
    state: 'Punjab',
    district: 'Ludhiana',
    primaryCrop: 'Wheat',
    avatar: '🚜',
    badgeColor: '#3B82F6',
    initialFarm: {
      estateName: "Gurpreet's Malwa Granary Farm",
      primaryCrop: 'Wheat',
      state: 'Punjab',
      area: 24.0,
      zones: [
        { id: 'zone-1', label: 'Canal Field', crop: 'Wheat', cropName: 'PBW-550 Wheat Acreage', area: '14.0 Ac' },
        { id: 'zone-2', label: 'North Block', crop: 'Mustard', cropName: 'Yellow Sarson Intercrop', area: '10.0 Ac' },
      ],
      timestamp: new Date().toISOString(),
    },
  },
]

/**
 * Initialize default farm profiles for preset demo accounts if not already saved.
 */
export function ensurePresetFarmsInitialized() {
  PRESET_FARMERS.forEach(f => {
    const key = `agri_farm_profile_${sanitizeUserId(f)}`
    if (!localStorage.getItem(key)) {
      localStorage.setItem(key, JSON.stringify(f.initialFarm))
    }
  })
}

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

