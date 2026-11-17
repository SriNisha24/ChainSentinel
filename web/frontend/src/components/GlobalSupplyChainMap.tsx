import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Globe,
  AlertTriangle,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Filter,
  Layers,
  Info
} from 'lucide-react';
import type { DatasetGeoResponse, GeoMarker, GeoFlow } from '../types/api';
import { api } from '../services/api';
import { WORLD_COUNTRIES } from '../assets/worldMapGeo';
import type { CountryGeoFeature } from '../assets/worldMapGeo';

// ============================================================================
// 1. COORDINATE PROJECTION (Matches worldMapGeo.ts equirectangular canvas)
// ============================================================================

function projectGeoToCanvas(lat: number, lon: number): { x: number; y: number } {
  // Clamped latitude between -65 and 84 degrees
  const clampedLat = Math.max(-65.0, Math.min(84.0, lat));
  // Standard equirectangular mapping onto 1000 x 500 canvas
  const x = Math.round(((lon + 180.0) / 360.0 * 1000.0) * 10) / 10;
  const y = Math.round(((84.0 - clampedLat) / 149.0 * 500.0) * 10) / 10;
  return { x, y };
}

// Generate smooth curved SVG Bézier path between two coordinates
function buildCurvedArcPath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);
  // Midpoint elevated upwards to create graceful trade flight curve
  const midX = (x1 + x2) / 2;
  const curveLift = Math.min(75, Math.max(25, dist * 0.22));
  const midY = (y1 + y2) / 2 - curveLift;
  return `M ${x1} ${y1} Q ${midX} ${midY} ${x2} ${y2}`;
}

// ============================================================================
// 2. MAIN COMPONENT
// ============================================================================

export interface GlobalSupplyChainMapProps {
  datasetId?: string;
  onSelectLocation?: (locationName: string) => void;
  className?: string;
  height?: string;
  context?: 'dataset_analysis' | 'analysis_results' | 'disruption_monitoring';
  activeDisruptionId?: string;
  selectedEntity?: string | null;
  onSelectEntity?: (details: string | null) => void;
}

export const GlobalSupplyChainMap: React.FC<GlobalSupplyChainMapProps> = ({
  datasetId = 'DS-ORIGINAL',
  onSelectLocation,
  className = '',
  height = 'min-h-[500px] lg:h-[580px]',
  context = 'dataset_analysis',
  activeDisruptionId,
  selectedEntity,
  onSelectEntity
}) => {
  // Map pan and zoom state
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState<number>(1.0);

  // Active filter state
  const [activeFilter, setActiveFilter] = useState<
    'all' | 'delayed' | 'non_delayed' | 'anomalies' | 'disruptions' | 'high_risk'
  >('all');

  // Backend geographic features payload
  const [geoData, setGeoData] = useState<DatasetGeoResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Hovered and Selected Marker state
  const [hoveredMarker, setHoveredMarker] = useState<GeoMarker | null>(null);
  const [selectedMarker, setSelectedMarker] = useState<GeoMarker | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);

  // Drag interaction refs
  const isDraggingRef = useRef<boolean>(false);
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const panStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch geographic features whenever datasetId or activeFilter changes
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    api.getDatasetGeoFeatures(datasetId, activeFilter, 5000)
      .then((data) => {
        if (!active) return;
        setGeoData(data);
        setLoading(false);
        if (context === 'disruption_monitoring' && data.markers.length > 0) {
          const hotspot = data.markers.find((m) => m.type === 'DISRUPTION_HOTSPOT');
          if (hotspot) {
            setSelectedMarker(hotspot);
          }
        }
      })
      .catch((err) => {
        if (!active) return;
        console.error('GeoService error:', err);
        setError('Failed to load geographic intelligence for this dataset.');
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [datasetId, activeFilter, context]);

  // Reset to initial centered full-world view
  const handleResetView = useCallback(() => {
    setPan({ x: 0, y: 0 });
    setZoom(1.0);
    setSelectedMarker(null);
  }, []);

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(3.5, z + 0.3));
  const handleZoomOut = () => setZoom((z) => Math.max(0.75, z - 0.3));

  // Pan interaction handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    // Only pan on primary left-click and not on buttons
    if (e.button !== 0) return;
    const target = e.target as HTMLElement;
    if (target.closest('button') || target.closest('.no-drag')) return;

    isDraggingRef.current = true;
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    panStartRef.current = { ...pan };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    const maxPanX = 500 * zoom;
    const maxPanY = 260 * zoom;
    setPan({
      x: Math.max(-maxPanX, Math.min(maxPanX, panStartRef.current.x + dx)),
      y: Math.max(-maxPanY, Math.min(maxPanY, panStartRef.current.y + dy))
    });
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    const delta = e.deltaY * -0.0015;
    setZoom((prevZoom) => Math.max(0.75, Math.min(3.5, prevZoom + delta)));
  };

  const handleDoubleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target.closest('button')) return;
    setZoom((z) => Math.min(3.5, z + 0.5));
  };

  // Zoom tier indicator
  const zoomTier = zoom < 1.4 ? 'GLOBAL VIEW' : zoom < 2.3 ? 'REGIONAL VIEW' : 'LOCAL HUB LEVEL';

  // Helper to format currency
  const formatUsd = (num: number) => `$${Math.round(num).toLocaleString()}`;

  // Filter options definitions
  const FILTER_OPTIONS = [
    { id: 'all', label: 'All Locations' },
    { id: 'delayed', label: 'Delayed Orders' },
    { id: 'non_delayed', label: 'On-Time Orders' },
    { id: 'anomalies', label: 'Profit Anomalies' },
    { id: 'disruptions', label: 'Disruption Hotspots' },
    { id: 'high_risk', label: 'High Revenue Exposure' },
  ];

  return (
    <div
      ref={containerRef}
      className={`relative w-full bg-[#060e1c] border border-slate-800/90 rounded-2xl shadow-sm overflow-hidden select-none flex flex-col justify-between ${height} ${className}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      onDoubleClick={handleDoubleClick}
      data-testid="global-supply-chain-map"
    >
      {/* ==================================================================== */}
      {/* 1. TOP HEADER: TITLE, DATASET ID, ZOOM TIER & VIEW CONTROLS          */}
      {/* ==================================================================== */}
      <div className="absolute top-3 left-4 right-4 z-20 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pointer-events-none">
        {/* Left: Map Title & Dataset Badge */}
        <div className="flex items-center gap-2">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-700/80 text-[11px] font-semibold text-slate-200 shadow-md">
            <Globe className="w-3.5 h-3.5 text-cyan-400" />
            <span>Global Supply-Chain Trade Map</span>
            <span className="text-slate-500">•</span>
            <span className="font-mono text-cyan-400 font-bold">{datasetId}</span>
          </div>

          {/* Zoom Tier Badge */}
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold bg-slate-800/85 border border-slate-700 text-slate-300 shadow-xs">
            <Layers className="w-3 h-3 text-cyan-400" />
            <span>{zoomTier}</span>
          </span>
        </div>

        {/* Right: Interaction & Zoom Controls */}
        <div className="flex items-center gap-1.5 pointer-events-auto">
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 backdrop-blur-md border border-slate-700 text-slate-300 hover:text-white transition shadow-md cursor-pointer"
            title="Zoom In"
            aria-label="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 backdrop-blur-md border border-slate-700 text-slate-300 hover:text-white transition shadow-md cursor-pointer"
            title="Zoom Out"
            aria-label="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetView}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 backdrop-blur-md border border-slate-700 text-[11px] font-semibold text-slate-300 hover:text-white transition shadow-md cursor-pointer"
            title="Reset Map to Full World View"
          >
            <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Reset View</span>
          </button>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* 2. CATEGORY FILTERS TOOLBAR                                         */}
      {/* ==================================================================== */}
      <div className="absolute top-13 left-4 z-20 pointer-events-auto flex flex-wrap items-center gap-1.5">
        <div className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-700 text-[10px] font-bold text-slate-400">
          <Filter className="w-3 h-3 text-slate-400" />
          <span>FILTER:</span>
        </div>
        {FILTER_OPTIONS.map((f) => {
          const isActive = activeFilter === f.id;
          return (
            <button
              key={f.id}
              onClick={() => setActiveFilter(f.id as any)}
              className={`px-2.5 py-1 rounded-xl text-[10px] font-semibold transition cursor-pointer shadow-sm ${
                isActive
                  ? 'bg-cyan-600 text-white font-bold border border-cyan-400 shadow-cyan-900/40 shadow-xs'
                  : 'bg-slate-900/85 hover:bg-slate-800 text-slate-300 border border-slate-700/80'
              }`}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center z-30 pointer-events-none">
          <div className="px-4 py-2.5 rounded-2xl bg-slate-900/90 border border-slate-700 text-xs font-semibold text-white flex items-center gap-2.5 shadow-xl">
            <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            <span>Mapping dataset geographic coordinates & trade flows...</span>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="absolute top-22 left-4 right-4 z-30 p-3 rounded-xl bg-rose-950/90 border border-rose-700 text-xs text-rose-200 flex items-center gap-2 shadow-xl">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Active entity banner notice if passed via props */}
      {selectedEntity && (
        <div className="absolute top-22 right-4 z-20 pointer-events-none px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-700 text-[11px] font-medium text-slate-300">
          <span className="text-cyan-400">Context:</span> {selectedEntity} {activeDisruptionId ? `(${activeDisruptionId})` : ''}
        </div>
      )}

      {/* Hovered Country Pill (Bottom Left when moving cursor over continents) */}
      {hoveredCountry && !hoveredMarker && (
        <div className="absolute bottom-16 left-4 z-20 pointer-events-none px-2.5 py-1 rounded-lg bg-slate-900/90 border border-slate-700 text-[11px] font-medium text-slate-300">
          <span className="text-cyan-400">Territory:</span> {hoveredCountry}
        </div>
      )}

      {/* ==================================================================== */}
      {/* 3. RECTANGULAR WORLD MAP SVG CANVAS                                  */}
      {/* ==================================================================== */}
      <div className="w-full h-full flex-1 relative overflow-hidden">
        <svg
          viewBox="0 0 1000 500"
          preserveAspectRatio="xMidYMid meet"
          className="w-full h-full"
        >
          <defs>
            {/* Deep dark rectangular ocean radial gradient background */}
            <radialGradient id="worldOceanGlow" cx="50%" cy="45%" r="65%">
              <stop offset="0%" stopColor="#0a203d" stopOpacity="0.9" />
              <stop offset="60%" stopColor="#07152b" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#040914" stopOpacity="1" />
            </radialGradient>

            {/* Neon Glow Filters */}
            <filter id="worldGlowRed" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="worldGlowCyan" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="worldGlowAmber" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Pulse Dash Animation for Trade Arcs */}
            <style>
              {`
                @keyframes worldFlowPulse {
                  from { stroke-dashoffset: 0; }
                  to { stroke-dashoffset: -140; }
                }
                .trade-flow-pulse {
                  animation: worldFlowPulse 3.5s linear infinite;
                }
              `}
            </style>
          </defs>

          {/* Deep Dark Navy Ocean Background */}
          <rect width="1000" height="500" fill="url(#worldOceanGlow)" />

          {/* Transform Container for Pan & Zoom */}
          <g
            transform={`translate(${500 + pan.x}, ${250 + pan.y}) scale(${zoom}) translate(-500, -250)`}
          >
            {/* -------------------------------------------------------------- */}
            {/* 3A. Rectangular Coordinate Graticule (Lat/Lon Grid)            */}
            {/* -------------------------------------------------------------- */}
            <g stroke="#0f223d" strokeWidth="0.75" strokeDasharray="3,5" fill="none">
              {/* Latitude lines */}
              <line x1="10" y1="80" x2="990" y2="80" />
              <line x1="10" y1="165" x2="990" y2="165" />
              <line x1="10" y1="250" x2="990" y2="250" />
              <line x1="10" y1="335" x2="990" y2="335" />
              <line x1="10" y1="420" x2="990" y2="420" />
              {/* Longitude lines */}
              <line x1="166" y1="10" x2="166" y2="490" />
              <line x1="333" y1="10" x2="333" y2="490" />
              <line x1="500" y1="10" x2="500" y2="490" />
              <line x1="666" y1="10" x2="666" y2="490" />
              <line x1="833" y1="10" x2="833" y2="490" />
            </g>

            {/* -------------------------------------------------------------- */}
            {/* 3B. GENUINE WORLD COUNTRIES & BOUNDARIES (From Natural Earth)  */}
            {/* -------------------------------------------------------------- */}
            <g id="world-countries-layer" fill="#081830" stroke="#132c52" strokeWidth="0.8">
              {WORLD_COUNTRIES.map((country: CountryGeoFeature) => (
                <path
                  key={country.id}
                  id={`country-${country.id}`}
                  d={country.path}
                  className="transition-colors hover:fill-[#0c264d] hover:stroke-[#38bdf8] cursor-pointer"
                  onMouseEnter={() => setHoveredCountry(country.name)}
                  onMouseLeave={() => setHoveredCountry(null)}
                />
              ))}
            </g>

            {/* Luminous Coastline Glow Highlights */}
            <g id="world-coastline-glow" fill="none" stroke="#0ea5e9" strokeWidth="0.7" opacity="0.4" pointerEvents="none">
              {WORLD_COUNTRIES.map((country: CountryGeoFeature) => (
                <path key={`glow-${country.id}`} d={country.path} />
              ))}
            </g>

            {/* -------------------------------------------------------------- */}
            {/* 3C. CONCEPTUAL TRADE FLOW ARCS (Dataset-Driven Arcs)           */}
            {/* -------------------------------------------------------------- */}
            <g id="trade-flows-layer" fill="none">
              {geoData?.flows.map((flow: GeoFlow) => {
                const pt1 = projectGeoToCanvas(flow.from_lat, flow.from_lon);
                const pt2 = projectGeoToCanvas(flow.to_lat, flow.to_lon);
                const arcPath = buildCurvedArcPath(pt1.x, pt1.y, pt2.x, pt2.y);
                const strokeColor = flow.is_disrupted ? '#ef4444' : '#06b6d4';
                const strokeFilter = flow.is_disrupted ? 'url(#worldGlowRed)' : 'url(#worldGlowCyan)';

                return (
                  <g key={flow.id}>
                    {/* Underlying Glow Arc */}
                    <path
                      d={arcPath}
                      stroke={strokeColor}
                      strokeWidth={flow.is_disrupted ? 2.2 : 1.7}
                      strokeDasharray="6,4"
                      filter={strokeFilter}
                      opacity={0.8}
                    />
                    {/* Animated Photon Pulse */}
                    <path
                      d={arcPath}
                      stroke="#ffffff"
                      strokeWidth={2.4}
                      strokeDasharray="14, 160"
                      className="trade-flow-pulse"
                      opacity={0.9}
                    />
                  </g>
                );
              })}
            </g>

            {/* -------------------------------------------------------------- */}
            {/* 3D. ACTIVE DISRUPTION HOTSPOTS (Expanding Ripples)             */}
            {/* -------------------------------------------------------------- */}
            {geoData?.markers
              .filter((m) => m.type === 'DISRUPTION_HOTSPOT')
              .map((hotspot) => {
                const pt = projectGeoToCanvas(hotspot.lat, hotspot.lon);
                return (
                  <g key={`hotspot_ripples_${hotspot.id}`} transform={`translate(${pt.x}, ${pt.y})`} fill="none">
                    <circle r="18" stroke="#ef4444" strokeWidth="1.8" opacity="0.8" />
                    <circle r="36" stroke="#ef4444" strokeWidth="1.2" opacity="0.5" strokeDasharray="4,4" />
                    <circle r="54" stroke="#f43f5e" strokeWidth="0.8" opacity="0.25" strokeDasharray="6,6" />
                  </g>
                );
              })}

            {/* -------------------------------------------------------------- */}
            {/* 3E. DATASET-DRIVEN GEOGRAPHIC MARKERS                           */}
            {/* -------------------------------------------------------------- */}
            <g id="markers-layer">
              {geoData?.markers.map((marker: GeoMarker) => {
                const pt = projectGeoToCanvas(marker.lat, marker.lon);
                const isSelected = selectedMarker?.id === marker.id;
                const isHovered = hoveredMarker?.id === marker.id;

                // Color & Icon Styling according to verified category
                let pinColor = '#06b6d4'; // Cyan default (Origin Coordinates)
                let filterGlow = 'url(#worldGlowCyan)';
                let radius = 6;

                if (marker.type === 'DISRUPTION_HOTSPOT') {
                  pinColor = '#ef4444'; // Red
                  filterGlow = 'url(#worldGlowRed)';
                  radius = 9;
                } else if (marker.type === 'DESTINATION_ORDER' || marker.type === 'CUSTOMER_CONSIGNEE') {
                  if (marker.delay_pct >= 50.0 || activeFilter === 'delayed') {
                    pinColor = '#f59e0b'; // Amber / High Delay Risk
                    filterGlow = 'url(#worldGlowAmber)';
                    radius = 7;
                  } else {
                    pinColor = '#3b82f6'; // Blue / Destination Country
                    radius = 5.5;
                  }
                }

                return (
                  <g
                    key={marker.id}
                    transform={`translate(${pt.x}, ${pt.y})`}
                    className="cursor-pointer transition-transform hover:scale-125"
                    onClick={() => {
                      setSelectedMarker(marker);
                      onSelectLocation?.(marker.name);
                      onSelectEntity?.(`${marker.name} (${marker.records_count.toLocaleString()} records, ${marker.delay_pct}% delayed)`);
                    }}
                    onMouseEnter={() => setHoveredMarker(marker)}
                    onMouseLeave={() => setHoveredMarker(null)}
                  >
                    {/* Glowing outer aura for selected or hovered */}
                    {(isSelected || isHovered) && (
                      <circle
                        r={radius + 8}
                        fill="none"
                        stroke={pinColor}
                        strokeWidth="2"
                        filter={filterGlow}
                        opacity="0.9"
                      />
                    )}

                    {/* Outer Pin Body */}
                    <circle
                      r={radius}
                      fill={pinColor}
                      filter={filterGlow}
                      stroke="#ffffff"
                      strokeWidth="1.2"
                    />

                    {/* Inner core */}
                    <circle r={radius * 0.4} fill="#060e1c" />

                    {/* Disruption Hotspot Center Badge & Callout (East Asia Port) */}
                    {marker.type === 'DISRUPTION_HOTSPOT' && (
                      <g transform="translate(14, -18)" className="pointer-events-none">
                        <rect
                          x="0"
                          y="0"
                          width="145"
                          height="36"
                          rx="8"
                          fill="#0f172a"
                          stroke="#ef4444"
                          strokeWidth="1.8"
                          filter="url(#worldGlowRed)"
                        />
                        <text x="10" y="16" fill="#ffffff" fontSize="10" fontWeight="bold" fontFamily="sans-serif">
                          {marker.name}
                        </text>
                        <text x="10" y="29" fill="#ef4444" fontSize="9" fontWeight="bold" fontFamily="sans-serif">
                          CLOSED (100%)
                        </text>
                      </g>
                    )}

                    {/* Location Name Label on hover, click, or when zoomed in */}
                    {(isSelected || isHovered || zoom >= 1.8) &&
                      marker.type !== 'DISRUPTION_HOTSPOT' && (
                        <g transform="translate(10, -8)" className="pointer-events-none">
                          <rect
                            x="-2"
                            y="-10"
                            width={marker.name.length * 6.5 + 10}
                            height="16"
                            rx="4"
                            fill="#091424"
                            stroke="#1e3a66"
                            strokeWidth="0.8"
                            opacity="0.92"
                          />
                          <text
                            x="4"
                            y="2"
                            fill="#e2e8f0"
                            fontSize="9"
                            fontWeight="600"
                            fontFamily="sans-serif"
                          >
                            {marker.name}
                          </text>
                        </g>
                      )}
                  </g>
                );
              })}
            </g>
          </g>
        </svg>

        {/* ================================================================== */}
        {/* 4. HOVER TOOLTIP (Instant quick inspection)                         */}
        {/* ================================================================== */}
        {hoveredMarker && (
          <div
            className="absolute top-14 right-4 z-30 bg-slate-900/95 backdrop-blur-md border border-slate-700/90 rounded-xl p-3 text-xs text-white shadow-2xl pointer-events-none max-w-xs animate-fade-in"
          >
            <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-1.5 mb-2">
              <span className="font-bold text-cyan-400 text-sm">{hoveredMarker.name}</span>
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${
                  hoveredMarker.type === 'DISRUPTION_HOTSPOT'
                    ? 'bg-red-950 text-red-300 border border-red-700'
                    : hoveredMarker.type === 'ORIGIN_HUB'
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-700'
                    : 'bg-blue-950 text-blue-300 border border-blue-700'
                }`}
              >
                {hoveredMarker.type.replace('_', ' ')}
              </span>
            </div>
            <div className="space-y-1 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Records:</span>
                <span className="font-semibold text-white">{hoveredMarker.records_count.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Delay Rate:</span>
                <span className={`font-semibold ${hoveredMarker.delay_pct > 50 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {hoveredMarker.delay_pct}% ({hoveredMarker.delayed_count} late)
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Revenue Exposure:</span>
                <span className="font-semibold text-white">{formatUsd(hoveredMarker.revenue_exposure_usd)}</span>
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/80">
                <span>Coordinates:</span>
                <span>{hoveredMarker.lat.toFixed(2)}°, {hoveredMarker.lon.toFixed(2)}°</span>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================== */}
        {/* 5. CLICKED MARKER DETAILS PANEL (Floating HUD)                    */}
        {/* ================================================================== */}
        {selectedMarker && (
          <div className="absolute top-24 left-4 z-30 bg-slate-900/95 backdrop-blur-md border border-cyan-500/50 rounded-2xl p-4 text-xs text-white shadow-2xl max-w-sm animate-fade-in pointer-events-auto">
            <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-2 mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-base text-cyan-400">{selectedMarker.name}</span>
                  {selectedMarker.type === 'DISRUPTION_HOTSPOT' && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-900/80 text-red-200 border border-red-500">
                      CRITICAL SHOCKWAVE
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-slate-400 font-medium mt-0.5">
                  {selectedMarker.type === 'ORIGIN_HUB'
                    ? 'Verified Origin Coordinates (Preserved)'
                    : selectedMarker.type === 'DISRUPTION_HOTSPOT'
                    ? 'Simulated Port Closure Disruption Source'
                    : 'Destination Country Centroid (Aggregated)'}
                </p>
              </div>
              <button
                onClick={() => setSelectedMarker(null)}
                className="text-slate-400 hover:text-white font-bold p-1 hover:bg-slate-800 rounded-lg transition cursor-pointer"
                title="Close Panel"
              >
                ✕
              </button>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-2 text-[11px] mb-3">
              <div className="p-2 rounded-xl bg-slate-800/70 border border-slate-700/60">
                <span className="text-slate-400 block text-[10px]">Associated Records</span>
                <span className="text-sm font-bold text-white">
                  {selectedMarker.records_count.toLocaleString()}
                </span>
              </div>
              <div className="p-2 rounded-xl bg-slate-800/70 border border-slate-700/60">
                <span className="text-slate-400 block text-[10px]">Delay Rate</span>
                <span className={`text-sm font-bold ${selectedMarker.delay_pct >= 50 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {selectedMarker.delay_pct}%
                </span>
              </div>
              <div className="p-2 rounded-xl bg-slate-800/70 border border-slate-700/60">
                <span className="text-slate-400 block text-[10px]">Delayed Orders</span>
                <span className="text-sm font-bold text-rose-300">
                  {selectedMarker.delayed_count.toLocaleString()}
                </span>
              </div>
              <div className="p-2 rounded-xl bg-slate-800/70 border border-slate-700/60">
                <span className="text-slate-400 block text-[10px]">Revenue Exposure</span>
                <span className="text-sm font-bold text-cyan-300">
                  {formatUsd(selectedMarker.revenue_exposure_usd)}
                </span>
              </div>
            </div>

            {/* Provenance and Coordinates */}
            <div className="p-2 rounded-xl bg-slate-950/70 border border-slate-800 text-[10px] space-y-1 text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Coordinates:</span>
                <span className="font-mono text-cyan-300">
                  {selectedMarker.lat.toFixed(3)}°N, {selectedMarker.lon.toFixed(3)}°E
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Data Source:</span>
                <span className="text-slate-300 font-semibold">{datasetId} ({activeFilter})</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ==================================================================== */}
      {/* 6. BOTTOM LEGEND & PROVENANCE NOTICE (Exact Match to Reference)     */}
      {/* ==================================================================== */}
      <div className="p-3 bg-slate-950/90 border-t border-slate-800/90 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs z-20">
        {/* Legend Symbols */}
        <div className="flex flex-wrap items-center gap-4 text-slate-300">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-cyan-500/50 shadow-xs" />
            <span className="font-medium text-[11px]">Origin Coordinates</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-blue-500/50 shadow-xs" />
            <span className="font-medium text-[11px]">Destination Country</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-amber-500/50 shadow-xs" />
            <span className="font-medium text-[11px]">High Delay Risk</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-red-500/50 shadow-xs" />
            <span className="font-medium text-[11px]">Disruption Hotspot</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 border-t-2 border-dashed border-cyan-400 inline-block" />
            <span className="font-medium text-[11px]">Trade Relationship</span>
          </div>
        </div>

        {/* Provenance Transparency Note */}
        <div className="text-[10px] text-slate-400 flex items-center gap-1.5">
          <Info className="w-3 h-3 text-slate-500 shrink-0" />
          <span>
            Geographic aggregation from selected dataset. Exact origin coordinates preserved; destinations clustered at centroids.
          </span>
        </div>
      </div>
    </div>
  );
};
export default GlobalSupplyChainMap;
