import { useState } from 'react'
import { LayoutDashboard, Map, Brain, Bell, FlaskConical, Users, BarChart3, Menu, X } from 'lucide-react'

const ITEMS = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { key: 'map', label: 'Risk Map', icon: Map },
  { key: 'predictions', label: 'Predictions', icon: Brain },
  { key: 'alerts', label: 'Alerts', icon: Bell },
  { key: 'simulator', label: 'What-If Simulator', icon: FlaskConical },
  { key: 'citizen', label: 'Citizen Mode', icon: Users },
  { key: 'analytics', label: 'Analytics', icon: BarChart3 },
]

export default function Sidebar({ active, onNavigate }) {
  const [open, setOpen] = useState(false)
  return (
    <>
    <button aria-label="Open navigation" onClick={() => setOpen(true)} className="sm:hidden fixed left-3 top-3 z-40 p-2 rounded-lg bg-slate-900 text-teal-300 border border-teal-900/60">
      <Menu size={19} />
    </button>
    {open && <button aria-label="Close navigation" onClick={() => setOpen(false)} className="sm:hidden fixed inset-0 z-30 bg-slate-950/60" />}
    <nav aria-label="Primary navigation" className={`bg-slate-900 border-r border-teal-950/70 w-56 shrink-0 flex flex-col gap-1 p-3 z-40 transition-transform sm:static sm:translate-x-0 ${open ? 'fixed inset-y-0 left-0 translate-x-0' : 'fixed inset-y-0 left-0 -translate-x-full'}`}>
      <div className="sm:hidden flex justify-end mb-2"><button aria-label="Close navigation" onClick={() => setOpen(false)} className="p-2 text-slate-400"><X size={19} /></button></div>
      {ITEMS.map(({ key, label, icon: Icon }) => (
        <button
          key={key}
          onClick={() => { onNavigate(key); setOpen(false) }}
          aria-current={active === key ? 'page' : undefined}
          title={label}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            active === key
              ? 'bg-teal-500/15 text-teal-300 border-l-2 border-teal-300'
              : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
          }`}
        >
          <Icon size={18} />
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </nav>
    </>
  )
}
