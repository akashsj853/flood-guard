import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { RISK_ORDER, RISK_COLORS } from '../data/demoData'
import { RiskBadge } from './ui'

export default function RiskOverview({ distribution }) {
  const data = RISK_ORDER.map((r) => ({ name: r, value: distribution?.[r] || 0 }))
  const total = data.reduce((s, d) => s + d.value, 0)

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <h2 className="text-sm font-semibold text-slate-300 mb-3">City-wide Risk Distribution</h2>
      {total === 0 ? (
        <p className="text-slate-500 text-sm py-6 text-center">No zones predicted yet.</p>
      ) : (
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <div className="w-full sm:w-40 h-40">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={data} dataKey="value" nameKey="name" innerRadius={40} outerRadius={70}>
                  {data.map((d) => (
                    <Cell key={d.name} fill={RISK_COLORS[d.name]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex-1 grid grid-cols-1 gap-1 w-full">
            {RISK_ORDER.map((r) => (
              <div key={r} className="flex items-center justify-between text-sm">
                <RiskBadge risk={r} />
                <span className="text-slate-400">{distribution?.[r] || 0} zones</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
