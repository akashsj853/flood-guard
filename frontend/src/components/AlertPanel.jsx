import { Bell, CheckCircle2 } from 'lucide-react'
import { RiskBadge } from './ui'

function fmtP(v) {
  const n = Number(v)
  return Number.isFinite(n) ? `${n.toFixed(1)}%` : '—'
}

// alerts: [{alert_id, zone_id, zone_name, risk_level, probability, recommendation,
//           reason, created_at, acknowledged, acknowledged_by}]
export default function AlertPanel({ alerts = [], onAcknowledge }) {
  if (!alerts.length) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-sm text-slate-500">
        No active alerts.
      </div>
    )
  }
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Bell size={16} className="text-amber-400" />
        <h2 className="text-sm font-semibold text-slate-300">Active Alerts ({alerts.length})</h2>
      </div>
      <ul className="flex flex-col gap-2">
        {alerts.map((a) => (
          <li key={a.alert_id} className="border border-slate-800 rounded-lg p-3 bg-slate-800/40">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-sm">{a.zone_name}</span>
              <RiskBadge risk={a.risk_level} />
            </div>
            {a.reason ? <p className="text-xs text-slate-400 mt-1">{a.reason}</p> : null}
            {a.recommendation ? <p className="text-xs text-slate-300 mt-1">{a.recommendation}</p> : null}
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                {a.acknowledged ? `✓ ${a.acknowledged_by || 'acknowledged'}` : `Prob ${fmtP(a.probability)}`}
              </span>
              {!a.acknowledged && onAcknowledge ? (
                <button
                  onClick={() => onAcknowledge(a.alert_id)}
                  className="flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white"
                >
                  <CheckCircle2 size={13} /> Ack
                </button>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
