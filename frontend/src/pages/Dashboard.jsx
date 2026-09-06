import { useEffect, useState } from 'react'
import { Activity } from 'lucide-react'
import * as api from '../services/api'
import RiskOverview from '../components/RiskOverview'
import WeatherPanel from '../components/WeatherPanel'
import ForecastRisk from '../components/ForecastRisk'
import RiskMap from '../components/RiskMap'
import AlertPanel from '../components/AlertPanel'
import { Loading, ErrorBox } from '../components/ui'

export default function Dashboard({ demo }) {
  const [overview, setOverview] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [weather, setWeather] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [ov, al, wx] = await Promise.all([
          api.getOverview(demo),
          api.getAlerts(demo),
          api.getWeatherCurrent({ latitude: 12.9719, longitude: 77.5937 }, demo).catch(() => null),
        ])
        if (cancelled) return
        setOverview(ov)
        setAlerts(al.alerts || [])
        setWeather(wx)
      } catch (e) {
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [demo])

  if (loading) return <Loading />
  if (error) return <ErrorBox message={error} />

  const zones = overview?.zones || []

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 text-slate-300">
        <Activity size={18} className="text-sky-400" />
        <h1 className="text-lg font-semibold">City Flood Dashboard</h1>
        {overview?.is_demo ? <span className="text-xs text-amber-400">(demo data)</span> : null}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <RiskOverview distribution={overview?.distribution} />
        <WeatherPanel weather={weather} />
        <div className="lg:col-span-1">
          <AlertSummary alerts={alerts} />
        </div>
      </div>

      <div>
        <h2 className="text-sm font-semibold text-slate-300 mb-2">Risk Map</h2>
        <RiskMap zones={zones} />
      </div>
    </div>
  )
}

function AlertSummary({ alerts }) {
  const top = (alerts || []).filter((a) => !a.acknowledged).slice(0, 5)
  if (!top.length) return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-sm text-slate-500">
      No active alerts.
    </div>
  )
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <h2 className="text-sm font-semibold text-slate-300 mb-3">Recent Alerts</h2>
      <ul className="flex flex-col gap-1.5">
        {top.map((a) => (
          <li key={a.alert_id} className="text-sm flex justify-between gap-2">
            <span>{a.zone_name}</span>
            <span className="text-slate-400">{a.risk_level}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
