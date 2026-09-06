import { CloudRain, Droplets, Wind, Thermometer, Gauge } from 'lucide-react'
import { fmtPct } from './ui'

function Stat({ icon: Icon, label, value, unit }) {
  return (
    <div className="bg-slate-800/60 rounded-lg p-3 flex flex-col gap-1">
      <div className="flex items-center gap-2 text-slate-400 text-xs">
        <Icon size={14} /> {label}
      </div>
      <div className="text-lg font-semibold">
        {value}
        <span className="text-xs text-slate-400 ml-1">{unit}</span>
      </div>
    </div>
  )
}

export default function WeatherPanel({ weather }) {
  if (!weather) return null
  const cur = weather.current || {}
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-300">Current Weather</h2>
        <span className="text-xs text-slate-500">
          source: {weather.source} {weather.is_demo ? '(demo)' : ''}
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <Stat icon={Thermometer} label="Temp" value={cur.temperature ?? '—'} unit="°C" />
        <Stat icon={Droplets} label="Humidity" value={cur.humidity ?? '—'} unit="%" />
        <Stat icon={Gauge} label="Pressure" value={cur.pressure ?? '—'} unit="hPa" />
        <Stat icon={Wind} label="Wind" value={cur.wind_speed ?? '—'} unit="km/h" />
        <Stat icon={CloudRain} label="Precip" value={cur.precipitation ?? '—'} unit="mm" />
      </div>
    </div>
  )
}
