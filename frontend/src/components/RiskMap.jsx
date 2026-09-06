import { MapContainer, TileLayer, CircleMarker, Tooltip, Popup } from 'react-leaflet'
import { riskColor } from './ui'

// zones: [{zone_id, zone_name, latitude, longitude, probability, risk, population_exposure_estimate}]
export default function RiskMap({ zones, center = [12.9719, 77.5937], onSelect }) {
  return (
    <div className="h-[70vh] w-full rounded-xl overflow-hidden border border-slate-800">
      <MapContainer center={center} zoom={11} scrollWheelZoom className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {zones.map((z) => {
          const lat = Number(z.latitude)
          const lon = Number(z.longitude)
          if (!lat || !lon) return null
          const c = riskColor(z.risk)
          const radius = 8 + Math.sqrt(Number(z.probability) || 0) * 1.6
          return (
            <CircleMarker
              key={z.zone_id}
              center={[lat, lon]}
              radius={radius}
              pathOptions={{ color: c, fillColor: c, fillOpacity: 0.6, weight: 2 }}
              eventHandlers={onSelect ? { click: () => onSelect(z) } : undefined}
            >
              <Tooltip>{z.zone_name}</Tooltip>
              <Popup>
                <div className="text-sm">
                  <strong>{z.zone_name}</strong>
                  <div>Risk: {z.risk}</div>
                  <div>Probability: {(Number(z.probability) || 0).toFixed(1)}%</div>
                  <div>Exposure: {Math.round(Number(z.population_exposure_estimate) || 0).toLocaleString()} people</div>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>
    </div>
  )
}
