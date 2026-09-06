import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { riskColor, RiskBadge } from './ui'

// forecast: {NOW:{probability,risk}, "+1 HOUR":..., "+3 HOURS":..., "+6 HOURS":...}
export default function ForecastRisk({ forecast }) {
  if (!forecast) return null
  const order = ['NOW', '+1 HOUR', '+3 HOURS', '+6 HOURS']
  const data = order
    .filter((k) => forecast[k])
    .map((k) => ({ label: k, probability: forecast[k].probability, risk: forecast[k].risk }))

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <h2 className="text-sm font-semibold text-slate-300 mb-3">Forecast Risk Timeline</h2>
      <div className="h-48">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
            <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={12} />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }}
              itemStyle={{ color: '#e2e8f0' }}
              formatter={(v) => [`${v}%`, 'Risk']}
            />
            <Line type="monotone" dataKey="probability" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap gap-2 mt-2">
        {data.map((d) => (
          <div key={d.label} className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">{d.label}</span>
            <RiskBadge risk={d.risk} />
            <span className="text-slate-300">{d.probability}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
