import { RISK_COLORS } from '../data/demoData'

export function riskColor(risk) {
  return RISK_COLORS[risk] || '#6b7280'
}

export function fmtPct(v) {
  return `${(Number(v) || 0).toFixed(1)}%`
}

export function classNames(...xs) {
  return xs.filter(Boolean).join(' ')
}

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="flex items-center gap-2 text-slate-400 py-8 justify-center">
      <span className="animate-spin h-4 w-4 border-2 border-slate-500 border-t-transparent rounded-full" />
      <span>{label}</span>
    </div>
  )
}

export function ErrorBox({ error }) {
  const msg = typeof error === 'string' ? error : error?.message || 'Something went wrong.'
  return (
    <div className="rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 px-4 py-3 text-sm">
      {msg}
    </div>
  )
}

export function Empty({ label = 'No data available.' }) {
  return <div className="text-slate-500 py-8 text-center text-sm">{label}</div>
}

export function RiskBadge({ risk }) {
  const c = riskColor(risk)
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold text-white"
      style={{ backgroundColor: c }}
    >
      {risk}
    </span>
  )
}
