import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts'
import { RISK_ORDER, RISK_COLORS } from '../data/demoData'

// analytics: {rainfall_last_24h, forecast_next_12h, zone_distribution, risk_trend, model_performance}
export default function Analytics({ analytics }) {
  if (!analytics) return null
  const dist = analytics.zone_distribution || {}
  const distData = RISK_ORDER.map((r) => ({ name: r, value: dist[r] || 0 }))
  const perf = analytics.model_performance || {}
  const perfRows = Object.entries(perf).filter(([k]) => k !== 'confusion_matrix')

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">Zone Risk Distribution</h2>
        <div className="h-56">
          <ResponsiveContainer>
            <BarChart data={distData} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
              <YAxis allowDecimals={false} stroke="#94a3b8" fontSize={11} />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} itemStyle={{ color: '#e2e8f0' }} />
              <Bar dataKey="value">
                {distData.map((d) => (
                  <Cell key={d.name} fill={RISK_COLORS[d.name]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">Model Performance</h2>
        {perfRows.length ? (
          <dl className="grid grid-cols-2 gap-2 text-sm">
            {perfRows.map(([k, v]) => (
              <div key={k} className="bg-slate-800/50 rounded-md px-3 py-2">
                <dt className="text-slate-400 text-xs">{k}</dt>
                <dd className="font-medium">{typeof v === 'number' ? v.toFixed(3) : String(v)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-sm text-slate-500">No trained model metrics available.</p>
        )}
      </div>

      {analytics.rainfall_last_24h?.length ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-300 mb-3">Rainfall — Last 24h by Zone</h2>
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={analytics.rainfall_last_24h} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="zone_id" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} itemStyle={{ color: '#e2e8f0' }} formatter={(v) => [`${v} mm`, 'Rainfall']} />
                <Bar dataKey="rainfall_24h" fill="#38bdf8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : null}
    </div>
  )
}
