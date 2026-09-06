import { Activity, LogOut, Moon, Radio, Sun, TestTube2 } from 'lucide-react'

export default function Navbar({ demo, onToggleDemo, theme, onToggleTheme, user, onLogout }) {
  return (
    <header className="bg-slate-900/90 border-b border-teal-900/50 px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 z-20 backdrop-blur">
      <div className="flex items-center gap-2">
      {user && <span className="hidden sm:inline text-xs text-slate-400">{user.username} · {user.role}</span>}
        <Activity className="text-sky-400" />
        <h1 className="font-display font-bold text-lg tracking-tight">FloodGuard AI</h1>
        <span className="text-xs text-slate-500 hidden sm:inline">
          Urban Flood Early Warning & Decision Support
        </span>
      </div>
      <div className="flex items-center gap-2">
      <button aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`} onClick={onToggleTheme} className="p-2 rounded-lg text-slate-400 hover:text-teal-300 hover:bg-slate-800">
        {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
      </button>
      <button
        onClick={onToggleDemo}
        aria-pressed={demo}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium border transition-colors ${
          demo
            ? 'border-amber-500/60 bg-amber-500/15 text-amber-300'
            : 'border-emerald-500/60 bg-emerald-500/15 text-emerald-300'
        }`}
        title="Toggle between live weather data and clearly-labelled offline demo data"
      >
        {demo ? <TestTube2 size={16} /> : <Radio size={16} />}
        {demo ? 'DEMO MODE (offline)' : 'LIVE MODE'}
      </button>
      <button aria-label="Sign out" onClick={onLogout} className="p-2 rounded-lg text-slate-400 hover:text-rose-300 hover:bg-slate-800"><LogOut size={17} /></button>
      </div>
    </header>
  )
}
