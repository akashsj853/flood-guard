import { useState } from 'react'
import { FlaskConical } from 'lucide-react'
import { RiskBadge, fmtPct } from './ui'

// zones: [{zone_id, zone_name}] for the selector
// onSimulate(zoneId, adjustments, demo) -> returns /api/simulation response
export default function WhatIfSimulator({ zones = [], demo, onSimulate, result, loading }) {
  const [zoneId, setZoneId] = useState(zones[0]?.zone_id || '')
  const [rainfall, setRainfall] = useState(1.0)
  const [drainage, setDrainage] = useState(0)
  const [impervious, setImpervious] = useState(0)

  const adjustments = {
    rainfall_multiplier: Number(rainfall),
    drainage_delta: Number(drainage),
    impervious_delta: Number(impervious),
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <FlaskConical size={16} className="text-violet-400" />
        <h2 className="text-sm font-semibold text-slate-300">What-If Simulator</h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="text-xs text-slate-400 flex flex-col gap-1">
          Zone
          <select
            value={zoneId}
            onChange={(e) => setZoneId(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-md px-2 py-1.5 text-sm text-slate-100"
          >
            {zones.map((z) => (
              <option key={z.zone_id} value={z.zone_id}>{z.zone_name}</option>
            ))}
          </select>
        </label>

        <label className="text-xs text-slate-400 flex flex-col gap-1">
          Rainfall multiplier: {rainfall.toFixed(2)}x
          <input type="range" min="0" max="3" step="0.1" value={rainfall}
            onChange={(e) => setRainfall(Number(e.target.value))} className="accent-violet-500" />
        </label>

        <label className="text-xs text-slate-400 flex flex-col gap-1">
          Drainage capacity delta: {drainage > 0 ? `+${drainage}` : drainage}
          <input type="range" min="-30" max="30" step="1" value={drainage}
            onChange={(e) => setDrainage(Number(e.target.value))} className="accent-violet-500" />
        </label>

        <label className="text-xs text-slate-400 flex flex-col gap-1">
          Impervious surface delta: {impervious > 0 ? `+${impervious}` : impervious}%
          <input type="range" min="-30" max="30" step="1" value={impervious}
            onChange={(e) => setImpervious(Number(e.target.value))} className="accent-violet-500" />
        </label>
      </div>

      <button
        disabled={loading || !zoneId}
        onClick={() => onSimulate(zoneId, adjustments, demo)}
        className="mt-3 w-full text-sm px-3 py-2 rounded-md bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-medium"
      >
        {loading ? 'Running…' : 'Run Simulation'}
      </button>

      {result ? (
        <div className="mt-3 border border-slate-800 rounded-lg p-3 bg-slate-800/40">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{result.zone_name}</span>
            <RiskBadge risk={result.scenario_risk} />
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
            <div className="bg-slate-800/60 rounded-md p-2">
              <div className="text-slate-400">Baseline</div>
              <div>{fmtPct(result.baseline_probability)} · <RiskBadge risk={result.baseline_risk} /></div>
            </div>
            <div className="bg-slate-800/60 rounded-md p-2">
              <div className="text-slate-400">Scenario</div>
              <div>{fmtPct(result.scenario_probability)} · <RiskBadge risk={result.scenario_risk} /></div>
            </div>
          </div>
          <div className="text-xs text-slate-400 mt-2">
            Δ probability: <span className="text-slate-200">{result.delta > 0 ? `+${result.delta}` : result.delta}%</span>
          </div>
        </div>
      ) : null}
    </div>
  )
}
