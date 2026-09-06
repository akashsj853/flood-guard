// Static fallback content used ONLY when the backend is unreachable.
// Clearly labelled as offline/demo so the UI never masquerades it as live data.

export const RISK_COLORS = {
  LOW: '#22c55e',
  MODERATE: '#eab308',
  HIGH: '#f97316',
  'VERY HIGH': '#ef4444',
  CRITICAL: '#b91c1c',
}

export const RISK_ORDER = ['LOW', 'MODERATE', 'HIGH', 'VERY HIGH', 'CRITICAL']

export const RECOMMENDATION_DISCLAIMER =
  'These are decision-support recommendations, not official emergency ' +
  'instructions. Follow directions from authorised disaster-management agencies.'

// Minimal demo zones (mirrors ml/data/zones.csv subset) so the map renders
// even with no backend. Coordinates are approximate city centroids.
export const DEMO_ZONES = [
  { zone_id: 'Z001', name: 'Central Business District', latitude: 12.9719, longitude: 77.5937, elevation: 920, slope: 2, drainage_capacity: 55, impervious_surface: 80, population: 45000, population_density: 18000, historical_flood_frequency: 6 },
  { zone_id: 'Z002', name: 'Majestic', latitude: 12.9767, longitude: 77.5727, elevation: 905, slope: 1, drainage_capacity: 40, impervious_surface: 88, population: 62000, population_density: 24000, historical_flood_frequency: 8 },
  { zone_id: 'Z003', name: 'KR Market', latitude: 12.9629, longitude: 77.5795, elevation: 900, slope: 1, drainage_capacity: 35, impervious_surface: 90, population: 51000, population_density: 21000, historical_flood_frequency: 9 },
  { zone_id: 'Z004', name: 'Indiranagar', latitude: 12.9784, longitude: 77.6408, elevation: 915, slope: 3, drainage_capacity: 60, impervious_surface: 70, population: 38000, population_density: 15000, historical_flood_frequency: 3 },
  { zone_id: 'Z005', name: 'Jayanagar', latitude: 12.9251, longitude: 77.5938, elevation: 905, slope: 2, drainage_capacity: 58, impervious_surface: 65, population: 41000, population_density: 16000, historical_flood_frequency: 4 },
]
