const defaultHost = typeof window !== 'undefined' && window.location?.hostname ? window.location.hostname : '127.0.0.1'
const isDevServer = typeof window !== 'undefined' && window.location?.port && window.location.port !== '8000'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (isDevServer ? '/api/v1' : `http://${defaultHost}:8000/api/v1`)
const ROOT_URL = API_BASE_URL.replace(/\/api\/v1\/?$/, '')

async function request(path, options = {}) {
  let url
  if (path.startsWith('http')) {
    url = path
  } else if (path.startsWith('/health')) {
    url = ROOT_URL ? `${ROOT_URL}${path}` : path
  } else {
    url = `${API_BASE_URL}${path}`
  }
  const headers = { ...options.headers }
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  const response = await fetch(url, {
    ...options,
    headers,
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg).join(', ')
      : body.detail
    throw new Error(detail || 'The advisory service could not complete that request.')
  }
  return body
}

export const cropApi = {
  schema: () => request('/crop/schema'),
  modelInfo: () => request('/crop/model-info'),
  recommend: (values) => request('/crop/recommend', { method: 'POST', body: JSON.stringify(values) }),
}

export const fertilizerApi = {
  schema: () => request('/fertilizer/schema'),
  modelInfo: () => request('/fertilizer/model-info'),
  example: () => request('/fertilizer/example'),
  recommend: (values) => request('/fertilizer/recommend', { method: 'POST', body: JSON.stringify(values) }),
}

export const advisoryApi = {
  unified: (values) => request('/advisory/unified', { method: 'POST', body: JSON.stringify(values) }),
}

export const healthApi = {
  status: () => request('/health'),
}

export const monitoringApi = {
  health: () => request('/monitoring/health'),
  latestDrift: () => request('/monitoring/drift/latest'),
  driftHistory: (lastN = 30) => request(`/monitoring/drift/history?last_n=${lastN}`),
  retrainHistory: (lastN = 20) => request(`/monitoring/retrain/history?last_n=${lastN}`),
  runDrift: () => request('/monitoring/drift/run', { method: 'POST', body: JSON.stringify({}) }),
  triggerRetrain: (force = false) => request('/monitoring/retrain/trigger', { method: 'POST', body: JSON.stringify({ force }) }),
}

export const farmApi = {
  zones: () => request('/farm/zones'),
  getZone: (zoneId) => request(`/farm/zones/${zoneId}`),
  ingestTelemetry: (zoneId, payload) => request(`/farm/zones/${zoneId}/telemetry`, { method: 'POST', body: JSON.stringify(payload) }),
  simulate: (zoneId, scenario = 'dry_spell') => request(`/farm/zones/${zoneId}/simulate?scenario=${scenario}`, { method: 'POST' }),
  advisory: (zoneId) => request(`/farm/zones/${zoneId}/advisory`),
  weather: (lat, lon) => request(`/farm/weather${lat && lon ? `?lat=${lat}&lon=${lon}` : ''}`),
}

export const pestRiskApi = {
  supportedProfiles: () => request('/pest-risk/supported-profiles'),
  assess: (payload) => request('/pest-risk/environmental-assessment', { method: 'POST', body: JSON.stringify(payload) }),
}

export const publicAdvisoriesApi = {
  list: (params = {}) => {
    const qry = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        qry.append(k, v)
      }
    })
    const qs = qry.toString()
    return request(`/public-advisories${qs ? `?${qs}` : ''}`)
  },
  summary: () => request('/public-advisories/summary'),
  sources: () => request('/public-advisories/sources'),
  get: (advisoryId) => request(`/public-advisories/${advisoryId}`),
  submitReview: (advisoryId, payload) =>
    request(`/public-advisories/${advisoryId}/review`, { method: 'POST', body: JSON.stringify(payload) }),
}

export const pestSurveillanceApi = {
  dashboard: () => request('/pest-surveillance/dashboard'),
  records: (params = {}) => {
    const qry = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        qry.append(k, v)
      }
    })
    const qs = qry.toString()
    return request(`/pest-surveillance/records${qs ? `?${qs}` : ''}`)
  },
  createRecord: (payload) =>
    request('/pest-surveillance/records', { method: 'POST', body: JSON.stringify(payload) }),
  uploadCsv: (formData) =>
    request('/pest-surveillance/upload-csv', { method: 'POST', body: formData }),
  reviewRecord: (payload) =>
    request('/pest-surveillance/review', { method: 'POST', body: JSON.stringify(payload) }),
  readinessGate: () => request('/pest-surveillance/readiness-gate'),
}



