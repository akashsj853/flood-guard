import { ArrowRight, MapPinned, ShieldCheck, Waves } from 'lucide-react'

export default function Landing({ onLogin, onRegister, onAdminLogin }) {
  return (
    <main className="min-h-screen bg-[#07141c] text-slate-100 overflow-hidden">
      <section className="max-w-6xl mx-auto px-6 py-10 sm:py-16">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-display font-bold text-xl"><Waves className="text-teal-300" /> FloodGuard AI</div>
          <div className="flex items-center gap-4"><button onClick={onLogin} className="text-sm text-teal-200 hover:text-white">Sign in</button><button onClick={onAdminLogin} className="text-sm text-slate-400 hover:text-white">Admin access</button></div>
        </header>
        <div className="grid lg:grid-cols-[1.1fr_.9fr] gap-12 items-center pt-20 pb-16">
          <div>
            <p className="text-xs uppercase tracking-[.2em] text-teal-300 mb-5">City-scale early warning</p>
            <h1 className="font-display text-5xl sm:text-7xl font-bold leading-[.98] max-w-3xl">Know the water before it moves.</h1>
            <p className="mt-6 text-lg text-slate-300 max-w-xl">Live weather, terrain intelligence, and clear next steps for every neighborhood in your city.</p>
            <div className="flex flex-wrap gap-3 mt-8">
              <button onClick={onRegister} className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-teal-400 text-[#062027] font-semibold hover:bg-teal-300">Create free account <ArrowRight size={17} /></button>
              <button onClick={onLogin} className="px-5 py-3 rounded-xl border border-teal-900 text-teal-100 hover:bg-teal-950/60">Sign in to dashboard</button>
            </div>
          </div>
          <div className="relative min-h-[330px] rounded-[2rem] border border-teal-900/70 bg-[radial-gradient(circle_at_30%_20%,#1c665e,transparent_35%),linear-gradient(145deg,#102d36,#07141c)] p-6 flex items-end">
            <div className="w-full rounded-2xl border border-white/10 bg-black/20 backdrop-blur p-5"><div className="flex justify-between text-xs text-teal-100"><span>LIVE CITY RISK</span><span>Updated now</span></div><div className="mt-7 h-3 rounded-full bg-gradient-to-r from-emerald-300 via-amber-300 to-rose-500" /><div className="flex justify-between mt-3 text-xs text-slate-300"><span>LOW</span><span>CRITICAL</span></div></div>
          </div>
        </div>
        <div className="grid sm:grid-cols-3 gap-4 border-t border-teal-950 pt-8 text-sm"><Feature icon={MapPinned} title="Neighborhood view" text="See risk by zone, not just by city." /><Feature icon={ShieldCheck} title="Clear decisions" text="Understand what is driving the forecast." /><Feature icon={Waves} title="Resilient by design" text="Demo data keeps the experience available." /></div>
      </section>
    </main>
  )
}

function Feature({ icon: Icon, title, text }) { return <div className="flex gap-3"><Icon className="text-teal-300 shrink-0" size={19} /><div><strong className="text-slate-100">{title}</strong><p className="text-slate-400 mt-1">{text}</p></div></div> }