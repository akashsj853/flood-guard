import { useEffect, useState } from 'react'
import { Brain } from 'lucide-react'
import * as api from '../services/api'
import ZoneDetails from '../components/ZoneDetails'
import ForecastRisk from '../components/ForecastRisk'
import RecommendationPanel from '../components/RecommendationPanel'
import { Loading, ErrorBox, RiskBadge, fmtPct } from '../components/ui'

export default function Predictions({ demo }) {
  const [zones, setZones] = useState([])
  const [selected, setSelected] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingPred, setLoadingPred] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const list = await api.getZones(demo)
        if (cancelled) return
        setZones(list || [])
        if (list?.length) select(list[0].zone_id, demo, setSelected, setPrediction, setLoadingPred, setError)
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

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 text-slate-300">
        <Brain size={18} className="text-sky-400" />
        <h1 className="text-lg font-semibold">Zone Predictions</h1>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {zones.map((z) => (
          <button
            key={z.zone_id}
            onClick={() => select(z.zone_id, demo, setSelected, setPrediction, setLoadingPred, setError)}
            className={`text-left text-sm px-3 py-2 rounded-md border ${
              selected?.zone_id === z.zone_id
                ? 'border-sky-500 bg-sky-600/10 text-sky-200'
                : 'border-slate-800 bg-slate-900 text-slate-300 hover:border-slate-700'
            }`}
          >
            {z.zone_name}
          </button>
        ))}
      </div>

      {loadingPred ? <Loading /> : null}

      {selected && prediction ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="flex flex-col gap-4">
            <ZoneDetails zone={selected} prediction={prediction} />
            <ForecastRisk forecast={prediction.forecast} />
          </div>
          <div className="flex flex-col gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Current prediction</span>
                <RiskBadge risk={prediction.risk} />
              </div>
              <div className="text-3xl font-bold mt-2">{fmtPct(prediction.probability)}</div>
              {prediction.model_type ? (
                <div className="text-xs text-slate-500 mt-1">model: {prediction.model_type}</div>
              ) : null}
              {prediction.is_demo ? (
                <div className="text-xs text-amber-400 mt-1">demo / fallback data</div>
              ) : null}
            </div>
            <RecommendationPanel prediction={prediction} />
          </div>
        </div>
      ) : null}
    </div>
  )
}

async function select(zoneId, demo, setSelected, setPrediction, setLoadingPred, setError) {
  try {
    setLoadingPred(true)
    const [full, pred] = await Promise.all([api.getZone(zoneId, demo), api.predict(zoneId, demo)])
    setSelected(full)
    setPrediction(pred)
  } catch (e) {
    setError(e.message)
  } finally {
    setLoadingPred(false)
  }
}
