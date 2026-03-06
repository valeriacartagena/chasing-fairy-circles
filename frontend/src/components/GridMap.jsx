import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';

// Fix for default leaflet marker icons failing to load in Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Auto-fit map bounds when features change
const MapFitter = ({ features }) => {
    const map = useMap();
    React.useEffect(() => {
        if (!features || features.length < 2) return;
        const lats = features.map(f => f.latitude);
        const lons = features.map(f => f.longitude);
        const bounds = L.latLngBounds(
            [Math.min(...lats) - 0.3, Math.min(...lons) - 0.3],
            [Math.max(...lats) + 0.3, Math.max(...lons) + 0.3]
        );
        map.flyToBounds(bounds, { duration: 1.0, padding: [20, 20] });
    }, [features, map]);
    return null;
};

const getColor = (b) => {
    if (b === undefined || isNaN(b)) return '#1e3a8a';
    if (b < 0.15) return '#1e3a8a';      // blue-900
    if (b < 0.35) return '#ca8a04';      // yellow-600
    return '#dc2626';                     // red-600
};

const makeCellIcon = (belief, icon) => {
    const color = getColor(belief);
    const label = icon || '';
    return L.divIcon({
        className: '',   // suppress Leaflet's default white box
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        html: `<div style="
      width:28px;height:28px;
      background:${color};
      border:1px solid rgba(255,255,255,0.2);
      border-radius:4px;
      display:flex;align-items:center;justify-content:center;
      font-size:14px;line-height:1;
      transition: background 0.3s ease;
      box-shadow: 0 2px 4px rgba(0,0,0,0.5);
    ">${label}</div>`,
    });
};

// ─────────────────────────────────────────────────────────────
const GridMap = ({ features, beliefs = [], actionsLog = [] }) => {
    const [selectedCell, setSelectedCell] = useState(null);

    if (!features || features.length === 0) {
        return (
            <div className="text-slate-500 flex items-center justify-center h-full text-sm">
                Loading region data...
            </div>
        );
    }

    const surveyedCells = new Set(actionsLog.filter(a => a.action === 'survey').map(a => a.cell));
    const drilledSuccess = new Set(actionsLog.filter(a => a.action === 'drill' && a.discovery).map(a => a.cell));
    const drilledFail = new Set(actionsLog.filter(a => a.action === 'drill' && !a.discovery).map(a => a.cell));

    const centerLat = features.reduce((s, f) => s + f.latitude, 0) / features.length;
    const centerLon = features.reduce((s, f) => s + f.longitude, 0) / features.length;

    return (
        <div className="relative w-full h-full rounded-lg overflow-hidden">
            <MapContainer
                center={[centerLat, centerLon]}
                zoom={7}
                style={{ width: '100%', height: '100%' }}
                zoomControl={true}
                attributionControl={false}
            >
                {/* ESRI Satellite imagery — no API key needed */}
                <TileLayer
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    maxZoom={18}
                />
                {/* Subtle label overlay */}
                <TileLayer
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
                    maxZoom={18}
                    opacity={0.55}
                />

                <MapFitter features={features} />

                {features.map((f) => {
                    const idx = f.cell_idx;
                    const belief = beliefs[idx] !== undefined ? beliefs[idx] : 0.2;

                    let icon = null;
                    if (drilledSuccess.has(idx)) icon = '🛢️';
                    else if (drilledFail.has(idx)) icon = '✗';
                    else if (surveyedCells.has(idx)) icon = '🔍';

                    return (
                        <Marker
                            key={`cell-${idx}`}
                            position={[f.latitude, f.longitude]}
                            icon={makeCellIcon(belief, icon)}
                            eventHandlers={{
                                click: () => setSelectedCell(selectedCell?.cell_idx === idx ? null : f),
                            }}
                        >
                            <Popup className="belief-popup">
                                <div style={{ fontFamily: 'monospace', fontSize: 12, minWidth: 180 }}>
                                    <div style={{ fontWeight: 'bold', marginBottom: 6 }}>
                                        Cell #{idx} {icon || ''}
                                    </div>
                                    <div>Belief: <b>{((belief) * 100).toFixed(1)}%</b></div>
                                    <div>Cluster: {f.cluster ?? '—'}</div>
                                    <div>Lat: {f.latitude?.toFixed(4)}</div>
                                    <div>Lon: {f.longitude?.toFixed(4)}</div>
                                    <div>PC1: {(f.pca_feature_1 ?? 0).toFixed(2)}</div>
                                    <div>PC2: {(f.pca_feature_2 ?? 0).toFixed(2)}</div>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>

            {/* Legend */}
            <div className="absolute bottom-3 left-3 z-[9999] bg-slate-900/85 border border-slate-700 rounded-md px-3 py-2 text-[10px] text-slate-400 flex items-center gap-3 backdrop-blur-sm pointer-events-none">
                <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm" style={{ background: '#1e3a8a' }}></div> Low</div>
                <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm" style={{ background: '#ca8a04' }}></div> Medium</div>
                <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm" style={{ background: '#dc2626' }}></div> High</div>
                <span className="ml-2 text-slate-500">Click cell for details</span>
            </div>
        </div>
    );
};

export default GridMap;
