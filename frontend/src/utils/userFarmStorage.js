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
