import { useEffect, useState } from 'react'
import * as api from '../services/api'
import WhatIfSimulator from '../components/WhatIfSimulator'
import { Loading, ErrorBox } from '../components/ui'

export default function Simulator({ demo }) {
  const [zones, setZones] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [simLoading, setSimLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const list = await api.getZones(demo)
        if (!cancelled) setZones(list || [])
      } catch (e) {
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [demo])

  async function run(zoneId, adjustments, demo) {
    setSimLoading(true)
    setError(null)
    try {
      const r = await api.simulate(zoneId, adjustments, demo)
      setResult(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setSimLoading(false)
    }
  }

  if (loading) return <Loading />
  if (error && !result) return <ErrorBox message={error} />

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-slate-300">What-If Simulator</h1>
      <p className="text-xs text-slate-500 max-w-2xl">
        Compare a baseline prediction against a scenario you define. Decision-support only —
        follow official disaster-management guidance.
      </p>
      <WhatIfSimulator
        zones={zones}
        demo={demo}
        onSimulate={run}
        result={result}
        loading={simLoading}
      />
    </div>
  )
}
