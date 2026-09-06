import { useEffect, useState } from 'react'
import { Bookmark, BellRing, Users, ShieldAlert } from 'lucide-react'
import * as api from '../services/api'
import { Loading, ErrorBox, RiskBadge, fmtPct } from '../components/ui'

// Plain-language public view. No internal jargon, no raw probabilities headline.
const MESSAGES = {
  LOW: 'Conditions are normal. No action needed.',
  MODERATE: 'Be aware. Watch for local waterlogging and avoid low-lying roads.',
  HIGH: 'Flooding is possible. Move vehicles to higher ground and avoid flooded stretches.',
  'VERY HIGH': 'Flooding is likely. Prepare to move to higher ground; keep emergency contacts handy.',
  CRITICAL: 'Severe flooding expected. Follow official instructions and evacuate if advised.',
}

export default function CitizenMode({ demo }) {
  const [zones, setZones] = useState([])
  const [zoneId, setZoneId] = useState('')
  const [pred, setPred] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState([])
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const list = await api.getZones(demo)
        if (cancelled) return
        setZones(list || [])
        api.getSavedLocations().then(setSaved).catch(() => {})
        if (list?.length) select(list[0].zone_id, demo, setPred, setError)
      } catch (e) {
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [demo])

  async function select(id, demo, setPred, setError) {
    setZoneId(id)
    try {
      const p = await api.predict(id, demo)
      setPred(p)
    } catch (e) {
      setError(e.message)
    }
  }

  if (loading) return <Loading />
  if (error) return <ErrorBox message={error} />
  if (!pred) return null

  const msg = MESSAGES[pred.risk] || MESSAGES.LOW

  async function saveCurrent() {
    try {
      const item = await api.saveLocation(zoneId, zones.find((z) => z.zone_id === zoneId)?.name || 'My area')
      setSaved((items) => [...items.filter((savedItem) => savedItem.zone_id !== item.zone_id), item])
      setNotice('Area saved to your profile.')
    } catch (e) { setNotice(e.response?.data?.detail || 'Could not save area.') }
  }

  async function subscribe() {
    try {
      await api.subscribeToZone(zoneId, pred.risk === 'LOW' ? 'MODERATE' : 'HIGH')
      setNotice('Risk alerts enabled for this area.')
    } catch (e) { setNotice(e.response?.data?.detail || 'Could not enable alerts.') }
  }

  return (
    <div className="flex flex-col gap-4 max-w-2xl mx-auto">
      <div className="flex items-center gap-2 text-slate-300">
        <Users size={18} className="text-emerald-400" />
        <h1 className="text-lg font-semibold">Citizen Flood Status</h1>
      </div>

      <label className="text-xs text-slate-400 flex flex-col gap-1">
        Your area
        <select
          value={zoneId}
          onChange={(e) => select(e.target.value, demo, setPred, setError)}
          className="bg-slate-800 border border-slate-700 rounded-md px-2 py-1.5 text-sm text-slate-100"
        >
          {zones.map((z) => (
            <option key={z.zone_id} value={z.zone_id}>{z.name}</option>
          ))}
        </select>
      </label>

      <div className="flex flex-wrap gap-2">
        <button onClick={saveCurrent} className="inline-flex items-center gap-2 rounded-lg border border-teal-900 px-3 py-2 text-sm text-teal-200 hover:bg-teal-950"><Bookmark size={15} /> Save this area</button>
        <button onClick={subscribe} className="inline-flex items-center gap-2 rounded-lg border border-teal-900 px-3 py-2 text-sm text-teal-200 hover:bg-teal-950"><BellRing size={15} /> Get risk alerts</button>
      </div>
      {notice && <p role="status" className="text-sm text-teal-300">{notice}</p>}
      {saved.length > 0 && <p className="text-xs text-slate-500">Saved areas: {saved.map((item) => item.label).join(' · ')}</p>}

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <ShieldAlert size={18} className="text-slate-400" />
          <RiskBadge risk={pred.risk} />
        </div>
        <p className="text-lg font-medium text-slate-100">{msg}</p>
        <p className="text-xs text-slate-500 mt-3">
          Risk level {pred.risk}. Current estimate {fmtPct(pred.probability)}.
          {pred.is_demo ? ' (demo data)' : ''}
        </p>
      </div>

      {pred.recommendations?.length ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h2 className="text-sm font-semibold text-slate-300 mb-2">What you can do</h2>
          <ul className="flex flex-col gap-1.5 text-sm text-slate-200">
            {pred.recommendations.map((r, i) => (
              <li key={i} className="flex gap-2"><span className="text-emerald-400">•</span><span>{r}</span></li>
            ))}
          </ul>
        </div>
      ) : null}

      <p className="text-[11px] text-slate-500">
        This is decision-support information, not an official warning. Always follow instructions
        from authorised disaster-management agencies.
      </p>
    </div>
  )
}
