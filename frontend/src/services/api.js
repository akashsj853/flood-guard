import axios from 'axios'

// All requests go through the Vite dev proxy -> FastAPI backend.
const client = axios.create({ baseURL: '/api', withCredentials: true })
client.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401) window.dispatchEvent(new Event('floodguard:unauthorized'))
  return Promise.reject(error)
})
const cache = new Map()
const pending = new Map()
const CACHE_TTL = 60_000

async function cachedGet(url, { ttl = CACHE_TTL } = {}) {
  const cached = cache.get(url)
  if (cached && Date.now() - cached.timestamp < ttl) return cached.data
  if (pending.has(url)) return pending.get(url)
  const request = client.get(url).then(({ data }) => {
    cache.set(url, { data, timestamp: Date.now() })
    pending.delete(url)
    return data
  }).catch((error) => {
    pending.delete(url)
    throw error
  })
  pending.set(url, request)
  return request
}

// Attach ?demo=true when in DEMO mode so the backend serves clearly-labelled
// offline data instead of calling a live weather provider.
function withDemo(url, demo) {
  return demo ? `${url}?demo=true` : url
}

export async function getHealth() {
  return cachedGet('/health', { ttl: 10_000 })
}

export async function getCurrentUser() {
  const { data } = await client.get('/auth/me')
  return data
}

export async function registerUser(payload) {
  const { data } = await client.post('/auth/register', payload)
  return data
}

export async function loginUser(payload) {
  const { data } = await client.post('/auth/login', payload)
  return data
}

export async function adminLogin(payload) {
  const { data } = await client.post('/auth/admin-login', payload)
  return data
}

export async function adminRegister(payload) {
  const { data } = await client.post('/auth/admin-register', payload)
  return data
}

export async function logoutUser() {
  const { data } = await client.post('/auth/logout')
  return data
}

export async function refreshAuth() {
  const { data } = await client.post('/auth/refresh')
  return data
}

export async function getSavedLocations() {
  const { data } = await client.get('/profile/locations')
  return data.locations
}

export async function saveLocation(zoneId, label) {
  const { data } = await client.post('/profile/locations', { zone_id: zoneId, label })
  return data
}

export async function subscribeToZone(zoneId, riskThreshold = 'HIGH') {
  const { data } = await client.post('/profile/subscriptions', { zone_id: zoneId, risk_threshold: riskThreshold, channels: ['in_app'] })
  return data
}

export async function getZoneHistory(zoneId, limit = 30) {
  const { data } = await client.get(`/zones/${zoneId}/history?limit=${limit}`)
  return data
}

export async function getZones(demo) {
  const data = await cachedGet(withDemo('/zones', demo), { ttl: 10 * 60_000 })
  return data.zones
}

export async function getZone(zoneId, demo) {
  return cachedGet(withDemo(`/zones/${zoneId}`, demo), { ttl: 10 * 60_000 })
}

export async function getWeatherCurrent(zone, demo) {
  return cachedGet(withDemo(`/weather/current?lat=${zone.latitude}&lon=${zone.longitude}`, demo))
}

export async function getWeatherForecast(zone, demo) {
  return cachedGet(withDemo(`/weather/forecast?lat=${zone.latitude}&lon=${zone.longitude}`, demo))
}

export async function getWeatherRainfall(zone, demo) {
  return cachedGet(withDemo(`/weather/rainfall?lat=${zone.latitude}&lon=${zone.longitude}`, demo))
}

export async function predict(zoneId, demo, scenario = null) {
  const { data } = await client.post(
    withDemo('/predict', demo),
    { zone_id: zoneId, scenario },
  )
  return data
}

export async function getOverview(demo) {
  return cachedGet(withDemo('/predictions/overview', demo), { ttl: 60_000 })
}

export async function getAlerts(demo) {
  return cachedGet(withDemo('/alerts', demo), { ttl: 30_000 })
}

export async function acknowledgeAlert(alertId) {
  const { data } = await client.post(`/alerts/${alertId}/acknowledge`)
  return data
}

export async function simulate(zoneId, adjustments, demo) {
  const { data } = await client.post(
    withDemo('/simulation', demo),
    { zone_id: zoneId, adjustments },
  )
  return data
}

export async function getAnalytics(demo) {
  return cachedGet(withDemo('/analytics', demo), { ttl: 60_000 })
}

export async function bulkPredict(zoneIds, demo, scenario = null) {
  const { data } = await client.post(withDemo('/predictions/bulk', demo), {
    zone_ids: zoneIds,
    scenario,
  })
  return data
}

export default client
