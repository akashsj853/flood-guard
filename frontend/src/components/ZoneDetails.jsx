import { RiskBadge, fmtPct } from './ui'

// zone: {zone_id, zone_name, latitude, longitude, elevation, slope, drainage_capacity,
//        impervious_surface, population, population_density, historical_flood_frequency}
// prediction: {probability, risk, forecast, population_exposure_estimate, risk_factors} (optional)
export default function ZoneDetails({ zone, prediction }) {
  if (!zone) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-sm text-slate-500">
        Select a zone on the map or from the list to see details.
      </div>
    )
  }
  const rows = [
    ['Elevation', `${zone.elevation ?? '—'} m`],
    ['Slope', `${zone.slope ?? '—'}°`],
    ['Drainage capacity', `${zone.drainage_capacity ?? '—'}`],
    ['Impervious surface', `${zone.impervious_surface ?? '—'}%`],
    ['Population', zone.population != null ? Number(zone.population).toLocaleString() : '—'],
    ['Population density', `${zone.population_density ?? '—'}/km²`],
    ['Historical flood freq.', `${zone.historical_flood_frequency ?? '—'}`],
  ]
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-300">{zone.zone_name}</h2>
        {prediction ? <RiskBadge risk={prediction.risk} /> : null}
      </div>
      <dl className="grid grid-cols-2 gap-2 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="bg-slate-800/50 rounded-md px-3 py-2">
            <dt className="text-slate-400 text-xs">{k}</dt>
            <dd className="font-medium">{v}</dd>
          </div>
        ))}
      </dl>
      {prediction ? (
        <div className="mt-3 text-sm bg-slate-800/50 rounded-md px-3 py-2">
          <div className="text-slate-400 text-xs">Current flood probability</div>
          <div className="font-semibold">{fmtPct(prediction.probability)}</div>
          {prediction.population_exposure_estimate != null ? (
            <div className="text-xs text-slate-400 mt-1">
              Est. exposure: {Number(prediction.population_exposure_estimate).toLocaleString()} people
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
