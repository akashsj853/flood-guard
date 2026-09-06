import { useEffect, useState } from 'react'
import { Bell } from 'lucide-react'
import * as api from '../services/api'
import AlertPanel from '../components/AlertPanel'
import { Loading, ErrorBox } from '../components/ui'

export default function Alerts({ demo }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => { load(demo, setAlerts, setLoading, setError) }, [demo])

  async function ack(alertId) {
    try {
      await api.acknowledgeAlert(alertId)
      load(demo, setAlerts, setLoading, setError)
    } catch (e) {
      setError(e.message)
    }
  }

  if (loading) return <Loading />
  if (error) return <ErrorBox message={error} />

  const active = alerts.filter((a) => !a.acknowledged).length

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 text-slate-300">
        <Bell size={18} className="text-amber-400" />
        <h1 className="text-lg font-semibold">Alerts</h1>
        <span className="text-xs text-slate-500">{active} active</span>
      </div>
      <AlertPanel alerts={alerts} onAcknowledge={ack} />
    </div>
  )
}

async function load(demo, setAlerts, setLoading, setError) {
  setLoading(true)
  setError(null)
  try {
    const data = await api.getAlerts(demo)
    setAlerts(data.alerts || [])
  } catch (e) {
    setError(e.message)
  } finally {
    setLoading(false)
  }
}
