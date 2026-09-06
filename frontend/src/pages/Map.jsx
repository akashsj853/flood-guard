import { useEffect, useState } from 'react'
import * as api from '../services/api'
import RiskMap from '../components/RiskMap'
import ZoneDetails from '../components/ZoneDetails'
import { Loading, ErrorBox } from '../components/ui'

export default function MapPage({ demo }) {
  const [zones, setZones] = useState([])
  const [details, setDetails] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const ov = await api.getOverview(demo)
        if (cancelled) return
        setZones(ov.zones || [])
      } catch (e) {
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [demo])

  async function selectZone(z) {
    setDetails(z)
    try {
      const full = await api.getZone(z.zone_id, demo)
      const pred = await api.predict(z.zone_id, demo)
      setDetails(full)
      setPrediction(pred)
    } catch (e) {
      setError(e.message)
    }
  }

  if (loading) return <Loading />
  if (error) return <ErrorBox message={error} />

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-slate-300">Risk Map</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <RiskMap zones={zones} onSelect={selectZone} />
        </div>
        <ZoneDetails zone={details} prediction={prediction} />
      </div>
    </div>
  )
}
