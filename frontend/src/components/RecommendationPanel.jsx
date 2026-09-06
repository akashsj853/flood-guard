import { Lightbulb } from 'lucide-react'
import { RECOMMENDATION_DISCLAIMER } from '../data/demoData'

// prediction: {risk_factors, recommendations?, explanation?, population_exposure_estimate}
// Either an explicit `recommendations` list or `reason` text is shown.
export default function RecommendationPanel({ prediction }) {
  const recs = prediction?.recommendations || []
  const reason = prediction?.reason || prediction?.explanation || ''
  if (!recs.length && !reason) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-sm text-slate-500">
        No recommendations available for this zone.
      </div>
    )
  }
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb size={16} className="text-sky-400" />
        <h2 className="text-sm font-semibold text-slate-300">Recommendations</h2>
      </div>
      {reason ? <p className="text-xs text-slate-400 mb-2">{reason}</p> : null}
      {recs.length ? (
        <ul className="flex flex-col gap-1.5">
          {recs.map((r, i) => (
            <li key={i} className="text-sm text-slate-200 flex gap-2">
              <span className="text-sky-400">•</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {prediction?.population_exposure_estimate != null ? (
        <p className="text-xs text-slate-400 mt-2">
          Est. population exposure: {Number(prediction.population_exposure_estimate).toLocaleString()} people
        </p>
      ) : null}
      <p className="text-[11px] text-slate-500 mt-3 border-t border-slate-800 pt-2">{RECOMMENDATION_DISCLAIMER}</p>
    </div>
  )
}
