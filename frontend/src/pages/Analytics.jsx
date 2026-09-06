import { useEffect, useState } from 'react'
import { BarChart3 } from 'lucide-react'
import * as api from '../services/api'
import Analytics from '../components/Analytics'
import RiskOverview from '../components/RiskOverview'
import { Loading, ErrorBox } from '../components/ui'
import { RECOMMENDATION_DISCLAIMER as DISCLAIMER } from '../data/demoData'

export default function AnalyticsPage({ demo }) {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await api.getAnalytics(demo)
        if (!cancelled) setAnalytics(data)
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
        <BarChart3 size={18} className="text-sky-400" />
        <h1 className="text-lg font-semibold">Analytics</h1>
      </div>
      <Analytics analytics={analytics} />
      <RiskOverview distribution={analytics?.zone_distribution} />
      <p className="text-[11px] text-slate-500">{DISCLAIMER}</p>
    </div>
  )
}
