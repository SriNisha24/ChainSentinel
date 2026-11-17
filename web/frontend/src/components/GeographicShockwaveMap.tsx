import React, { useState, useRef, useCallback } from 'react';
import {
  Anchor,
  Factory,
  Warehouse,
  Truck,
  Ship,
  Plane,
  Users,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Compass,
  Info
} from 'lucide-react';

interface GeographicShockwaveMapProps {
  onSelectEntity?: (details: string | null) => void;
  selectedEntity?: string | null;
  capacityLoss?: string;
  eventName?: string;
  eventId?: string;
}

export const GeographicShockwaveMap: React.FC<GeographicShockwaveMapProps> = ({
  onSelectEntity,
  selectedEntity,
  capacityLoss = '100%',
  eventName = 'East Asia Port',
  eventId = 'SIM-DISR-2026-001'
}) => {
  // Map pan and zoom state
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState<number>(1.0);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const isDraggingRef = useRef<boolean>(false);
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const panStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Reset to initial centered view
  const handleResetView = useCallback(() => {
    setPan({ x: 0, y: 0 });
    setZoom(1.0);
  }, []);

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(2.5, z + 0.2));
  const handleZoomOut = () => setZoom((z) => Math.max(0.75, z - 0.2));

  // Pan interaction handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0) return; // Only left-click
    isDraggingRef.current = true;
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    panStartRef.current = { ...pan };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    // Clamped pan range to keep Asia map framed
    const maxPanX = 350 * zoom;
    const maxPanY = 220 * zoom;
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
    setZoom((prevZoom) => Math.max(0.75, Math.min(2.5, prevZoom + delta)));
  };

  return (
    <div
      className="relative w-full h-full min-h-[460px] lg:h-[500px] bg-[#060e1c] overflow-hidden select-none cursor-grab active:cursor-grabbing flex flex-col justify-between"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
    >
      {/* ==================================================================== */}
      {/* 1. TOP INTERACTION CONTROLS & HUD OVERLAY                           */}
      {/* ==================================================================== */}
      <div className="absolute top-3 left-4 right-4 flex items-center justify-between pointer-events-none z-20">
        {/* Interaction Notification Pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/85 backdrop-blur-md border border-slate-700/80 text-[11px] font-medium text-slate-300 shadow-md">
          <Compass className="w-3.5 h-3.5 text-cyan-400" />
          <span>Asia Geographic Disruption Map</span>
          <span className="hidden sm:inline text-slate-500">• Drag to pan • Scroll to zoom</span>
        </div>

        {/* Viewport Action Buttons */}
        <div className="flex items-center gap-1.5 pointer-events-auto">
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded-xl bg-slate-900/85 hover:bg-slate-800 backdrop-blur-md border border-slate-700/80 text-slate-300 hover:text-white transition shadow-md cursor-pointer"
            title="Zoom In"
            aria-label="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded-xl bg-slate-900/85 hover:bg-slate-800 backdrop-blur-md border border-slate-700/80 text-slate-300 hover:text-white transition shadow-md cursor-pointer"
            title="Zoom Out"
            aria-label="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetView}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-900/85 hover:bg-slate-800 backdrop-blur-md border border-slate-700/80 text-[11px] font-semibold text-slate-300 hover:text-white transition shadow-md cursor-pointer"
            title="Reset Map to Original Center"
          >
            <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Reset View</span>
          </button>
        </div>
      </div>

      {/* Selected Entity Notification banner if user clicks a node */}
      {selectedEntity && (
        <div className="absolute top-12 left-4 z-30 bg-slate-900/90 backdrop-blur-md border border-slate-700/90 rounded-xl px-3.5 py-2 text-xs text-white flex items-center gap-2.5 shadow-xl max-w-md animate-fade-in pointer-events-auto">
          <Info className="w-4 h-4 text-cyan-400 shrink-0" />
          <span className="line-clamp-2 leading-relaxed">{selectedEntity}</span>
          <button
            onClick={() => onSelectEntity?.(null)}
            className="ml-auto text-slate-400 hover:text-white font-bold px-1.5 py-0.5 rounded cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* ==================================================================== */}
      {/* 2. RECTANGULAR ASIA GEOGRAPHIC MAP CANVAS (SVG)                      */}
      {/* ==================================================================== */}
      <div className="w-full h-full flex-1 relative overflow-hidden">
        <svg
          viewBox="0 0 960 520"
          preserveAspectRatio="xMidYMid meet"
          className="w-full h-full"
        >
          <defs>
            {/* Deep dark rectangular radial gradient background */}
            <radialGradient id="rectOceanGlow" cx="52%" cy="46%" r="58%">
              <stop offset="0%" stopColor="#0c213d" stopOpacity="0.85" />
              <stop offset="50%" stopColor="#07152b" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#040914" stopOpacity="1" />
            </radialGradient>

            {/* Neon Glow Filters */}
            <filter id="glowRed" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <filter id="glowYellow" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <filter id="glowCyan" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <filter id="glowPurple" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Animated Pulses Style */}
            <style>
              {`
                @keyframes pulseDash {
                  from { stroke-dashoffset: 0; }
                  to { stroke-dashoffset: -120; }
                }
                .flowing-pulse {
                  animation: pulseDash 3.5s linear infinite;
                }
                .flowing-pulse-fast {
                  animation: pulseDash 2.5s linear infinite;
                }
              `}
            </style>
          </defs>

          {/* Rectangular Ocean Background filling entire card */}
          <rect width="960" height="520" fill="url(#rectOceanGlow)" />

          {/* Interactive Transform Container for Pan & Zoom */}
          <g
            transform={`translate(${480 + pan.x}, ${260 + pan.y}) scale(${zoom}) translate(-480, -260)`}
          >
            {/* -------------------------------------------------------------- */}
            {/* 2A. RECTANGULAR GEOGRAPHIC LAT/LON COORDINATE GRATICULE        */}
            {/* -------------------------------------------------------------- */}
            <g stroke="#112442" strokeWidth="0.8" strokeDasharray="4,6" fill="none">
              {/* Latitude lines */}
              <line x1="20" y1="90" x2="940" y2="90" />
              <line x1="20" y1="180" x2="940" y2="180" />
              <line x1="20" y1="270" x2="940" y2="270" />
              <line x1="20" y1="360" x2="940" y2="360" />
              <line x1="20" y1="450" x2="940" y2="450" />
              {/* Longitude lines */}
              <line x1="160" y1="30" x2="160" y2="490" />
              <line x1="320" y1="30" x2="320" y2="490" />
              <line x1="480" y1="30" x2="480" y2="490" />
              <line x1="640" y1="30" x2="640" y2="490" />
              <line x1="800" y1="30" x2="800" y2="490" />
            </g>

            {/* -------------------------------------------------------------- */}
            {/* 2B. AUTHENTIC ASIA GEOGRAPHIC LANDMASSES & COASTLINES           */}
            {/* -------------------------------------------------------------- */}
            <g
              id="asia-landmass-layer"
              fill="#0a1a33"
              stroke="#1b3966"
              strokeWidth="1.2"
              className="transition-colors"
            >
              {/* 1. Siberia / Northern Asia Plate */}
              <path d="M 60 45 Q 200 35 380 42 Q 540 25 720 40 Q 840 50 920 85 L 900 125 Q 780 135 690 145 Q 560 155 440 135 Q 280 120 160 150 Q 80 170 60 135 Z" />

              {/* 2. Central Asia & Mainland China Continental Landmass */}
              <path d="M 100 165 Q 240 140 380 148 Q 500 155 600 175 Q 630 210 590 250 Q 550 290 490 310 Q 430 335 350 315 Q 250 295 190 245 Q 90 210 100 165 Z" />

              {/* 3. Detailed East Asia Coastline (Bohai Bay, Shandong, Yellow Sea, Yangtze Delta, East China Sea, South China Sea) */}
              <path d="M 480 160 Q 530 175 560 190 Q 580 215 570 235 Q 560 250 540 265 Q 530 290 515 320 Q 490 350 460 380 Q 435 340 450 310 Q 480 280 505 240 Q 515 200 480 160 Z" />

              {/* 4. Korean Peninsula */}
              <path d="M 565 178 Q 588 195 582 225 Q 572 238 560 220 Q 556 195 565 178 Z" />

              {/* 5. Japanese Archipelago (Honshu, Hokkaido, Kyushu) */}
              <path d="M 635 168 Q 658 185 648 215 Q 628 235 618 225 Q 628 198 635 168 Z" />
              <path d="M 655 138 Q 675 148 665 162 Q 650 158 655 138 Z" />
              <path d="M 610 228 Q 622 238 615 250 Q 604 245 610 228 Z" />

              {/* 6. Taiwan Island */}
              <path d="M 545 285 Q 552 295 548 310 Q 540 312 538 300 Q 540 288 545 285 Z" />

              {/* 7. Indian Subcontinent & Sri Lanka */}
              <path d="M 260 275 Q 320 285 350 325 Q 340 385 310 418 Q 280 380 270 338 Q 250 298 260 275 Z" />
              <circle cx="312" cy="432" r="6" />

              {/* 8. Indochina & Southeast Asia Mainland (Vietnam, Thailand, Cambodia, Myanmar) */}
              <path d="M 430 295 Q 470 305 480 355 Q 460 405 430 425 Q 410 385 420 345 Z" />

              {/* 9. Malay Peninsula */}
              <path d="M 432 425 Q 448 450 442 478 L 434 475 Q 425 445 432 425 Z" />

              {/* 10. Indonesian Archipelago (Sumatra, Java, Borneo, Sulawesi) */}
              <path d="M 460 450 Q 530 442 570 460 Q 520 475 460 450 Z" />
              <path d="M 510 480 Q 590 475 630 490 Q 560 505 510 480 Z" />
              <path d="M 515 390 Q 555 385 575 415 Q 545 435 515 390 Z" />

              {/* 11. Philippines Archipelago (Luzon, Mindanao) */}
              <path d="M 610 335 Q 630 355 620 395 Q 608 375 610 335 Z" />
              <path d="M 618 405 Q 632 420 622 438 Q 612 425 618 405 Z" />
            </g>

            {/* Luminous Coastline Edge Highlight (Glowing Blue/Cyan borders) */}
            <g fill="none" stroke="#0ea5e9" strokeWidth="1.2" opacity="0.45">
              <path d="M 480 160 Q 530 175 560 190 Q 580 215 570 235 Q 560 250 540 265 Q 530 290 515 320 Q 490 350 460 380" />
              <path d="M 565 178 Q 588 195 582 225 Q 572 238 560 220" />
              <path d="M 635 168 Q 658 185 648 215 Q 628 235 618 225" />
              <path d="M 260 275 Q 320 285 350 325 Q 340 385 310 418" />
              <path d="M 430 295 Q 470 305 480 355 Q 460 405 430 425" />
            </g>

            {/* -------------------------------------------------------------- */}
            {/* 2C. GLOWING CONNECTING PATHS & ANIMATED LIGHT PULSES           */}
            {/* -------------------------------------------------------------- */}
            <g id="connecting-paths-layer" fill="none">
              {/* Path 1: Central Port -> Factory 1 (Inland Northwest) [Yellow/Orange Dashed] */}
              <path
                id="p_port_factory1"
                d="M 520 240 Q 380 150 265 115"
                stroke="#f59e0b"
                strokeWidth="2.5"
                strokeDasharray="7,5"
                filter="url(#glowYellow)"
              />
              <path
                d="M 520 240 Q 380 150 265 115"
                stroke="#ffffff"
                strokeWidth="2.8"
                strokeDasharray="14, 180"
                className="flowing-pulse"
                opacity="0.9"
              />

              {/* Path 2: Inter-factory connector / Transport -> Factory 2 [Cyan Dashed] */}
              <path
                id="p_trans_factory2"
                d="M 345 315 Q 260 280 235 225"
                stroke="#0ea5e9"
                strokeWidth="2"
                strokeDasharray="6,4"
                filter="url(#glowCyan)"
              />

              {/* Path 3: Central Port -> Road Transport (Truck) [Cyan Dashed] */}
              <path
                id="p_port_truck"
                d="M 520 240 Q 425 285 345 315"
                stroke="#06b6d4"
                strokeWidth="2.5"
                strokeDasharray="6,4"
                filter="url(#glowCyan)"
              />
              <path
                d="M 520 240 Q 425 285 345 315"
                stroke="#ffffff"
                strokeWidth="2.8"
                strokeDasharray="12, 140"
                className="flowing-pulse-fast"
                opacity="0.9"
              />

              {/* Path 4: Central Port -> Transit point [Cyan dotted] */}
              <path
                id="p_port_transit"
                d="M 520 240 Q 460 190 395 180"
                stroke="#38bdf8"
                strokeWidth="1.8"
                strokeDasharray="4,4"
                filter="url(#glowCyan)"
              />

              {/* Path 5: Central Port -> Air Freight [Solid Cyan] */}
              <path
                id="p_port_air"
                d="M 520 240 Q 470 305 435 365"
                stroke="#38bdf8"
                strokeWidth="2.5"
                filter="url(#glowCyan)"
              />
              <path
                d="M 520 240 Q 470 305 435 365"
                stroke="#ffffff"
                strokeWidth="3.0"
                strokeDasharray="15, 150"
                className="flowing-pulse"
                opacity="0.95"
              />

              {/* Path 6: Central Port -> Warehouse (South) [Pink/Red Dashed] */}
              <path
                id="p_port_wh"
                d="M 520 240 Q 515 330 510 420"
                stroke="#f43f5e"
                strokeWidth="2.5"
                strokeDasharray="6,4"
                filter="url(#glowRed)"
              />
              <path
                d="M 520 240 Q 515 330 510 420"
                stroke="#ffffff"
                strokeWidth="2.8"
                strokeDasharray="14, 160"
                className="flowing-pulse"
                opacity="0.9"
              />

              {/* Path 7: Central Port -> Customer (Southeast) [Red/Pink Dashed] */}
              <path
                id="p_port_cust"
                d="M 520 240 Q 600 325 650 420"
                stroke="#ef4444"
                strokeWidth="2.5"
                strokeDasharray="6,4"
                filter="url(#glowRed)"
              />
              <path
                d="M 520 240 Q 600 325 650 420"
                stroke="#ffffff"
                strokeWidth="2.8"
                strokeDasharray="16, 170"
                className="flowing-pulse-fast"
                opacity="0.9"
              />

              {/* Path 8: Central Port -> Cargo Ship 1 (Northeast Pacific) [Solid Cyan] */}
              <path
                id="p_port_ship1"
                d="M 520 240 Q 615 180 700 170"
                stroke="#06b6d4"
                strokeWidth="2.5"
                filter="url(#glowCyan)"
              />
              <path
                d="M 520 240 Q 615 180 700 170"
                stroke="#ffffff"
                strokeWidth="3.0"
                strokeDasharray="15, 160"
                className="flowing-pulse"
                opacity="0.9"
              />

              {/* Path 9: Central Port -> Cargo Ship 2 (Central Pacific) [Cyan Dashed] */}
              <path
                id="p_port_ship2"
                d="M 520 240 Q 595 260 670 290"
                stroke="#06b6d4"
                strokeWidth="2"
                strokeDasharray="6,4"
                filter="url(#glowCyan)"
              />
            </g>

            {/* -------------------------------------------------------------- */}
            {/* 2D. CONCENTRIC SHOCKWAVE RIPPLES AT PORT ORIGIN                */}
            {/* -------------------------------------------------------------- */}
            <g id="shockwave-ripples-layer" transform="translate(520, 240)" fill="none">
              <circle r="45" stroke="#ef4444" strokeWidth="1.8" opacity="0.8" />
              <circle r="75" stroke="#ef4444" strokeWidth="1.4" opacity="0.5" strokeDasharray="5,5" />
              <circle r="110" stroke="#ef4444" strokeWidth="1.0" opacity="0.3" strokeDasharray="6,6" />
              <circle r="150" stroke="#f43f5e" strokeWidth="0.8" opacity="0.15" />
            </g>

            {/* -------------------------------------------------------------- */}
            {/* 2E. HAZARD WARNING BEACON (YELLOW SEA / KOREA STRAIT)          */}
            {/* -------------------------------------------------------------- */}
            <g
              id="hazard-warning-beacon"
              transform="translate(555, 160)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Hazard Zone: Coastal shipping lanes compromised due to primary port blackout (Yellow Sea corridor).'
                )
              }
              onMouseEnter={() => setHoveredNode('hazard')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <polygon
                points="0,-18 16,12 -16,12"
                fill="rgba(239, 68, 68, 0.25)"
                stroke="#ef4444"
                strokeWidth="2.5"
                filter="url(#glowRed)"
                className="group-hover:fill-red-900/60 transition"
              />
              <line
                x1="0"
                y1="-8"
                x2="0"
                y2="2"
                stroke="#ffffff"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              <circle cx="0" cy="7" r="1.5" fill="#ffffff" />

              {hoveredNode === 'hazard' && (
                <g transform="translate(0, -28)">
                  <rect
                    x="-55"
                    y="-16"
                    width="110"
                    height="20"
                    rx="5"
                    fill="#0f172a"
                    stroke="#ef4444"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    Hazard Warning
                  </text>
                </g>
              )}
            </g>

            {/* -------------------------------------------------------------- */}
            {/* 2F. RECOGNIZABLE SUPPLY CHAIN ENTITY SYMBOLS (NOT GENERIC DOTS) */}
            {/* -------------------------------------------------------------- */}

            {/* NODE 1: Factory 1 (Inland Northwest) */}
            <g
              id="node-factory-1"
              transform="translate(265, 115)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Factory 1: 42 SKU Manufacturing Lines (Inland Production Tier 1, Shaanxi)'
                )
              }
              onMouseEnter={() => setHoveredNode('factory_1')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <circle
                r="27"
                fill="#181308"
                stroke="#f59e0b"
                strokeWidth="2"
                filter="url(#glowYellow)"
                className="group-hover:scale-110 transition-transform origin-center"
              />
              <circle
                r="22"
                fill="none"
                stroke="#f59e0b"
                strokeWidth="1"
                strokeDasharray="3,3"
                opacity="0.6"
              />
              <g transform="translate(-11, -11) scale(0.9)">
                <path
                  d="M2 20h20M7 20v-5l5 2v-4l5 2v-4l5 2v7M7 8V4h4v2"
                  fill="none"
                  stroke="#fbbf24"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
              {hoveredNode === 'factory_1' && (
                <g transform="translate(0, -36)">
                  <rect
                    x="-60"
                    y="-16"
                    width="120"
                    height="20"
                    rx="5"
                    fill="#0f172a"
                    stroke="#f59e0b"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill="#fbbf24"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    Factory 1 (Tier-1)
                  </text>
                </g>
              )}
            </g>

            {/* NODE 2: Factory 2 (Central West) */}
            <g
              id="node-factory-2"
              transform="translate(235, 225)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Factory 2: 29 SKU Electronics & Equipment Production (Tier 2 Origin, Sichuan)'
                )
              }
              onMouseEnter={() => setHoveredNode('factory_2')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <circle
                r="27"
                fill="#181308"
                stroke="#f59e0b"
                strokeWidth="2"
                filter="url(#glowYellow)"
                className="group-hover:scale-110 transition-transform origin-center"
              />
              <circle
                r="22"
                fill="none"
                stroke="#f59e0b"
                strokeWidth="1"
                strokeDasharray="3,3"
                opacity="0.6"
              />
              <g transform="translate(-11, -11) scale(0.9)">
                <path
                  d="M2 20h20M7 20v-5l5 2v-4l5 2v-4l5 2v7M7 8V4h4v2"
                  fill="none"
                  stroke="#fbbf24"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
              {hoveredNode === 'factory_2' && (
                <g transform="translate(0, -36)">
                  <rect
                    x="-60"
                    y="-16"
                    width="120"
                    height="20"
                    rx="5"
                    fill="#0f172a"
                    stroke="#f59e0b"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill="#fbbf24"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    Factory 2 (Tier-2)
                  </text>
                </g>
              )}
            </g>

            {/* NODE 3: Transport / Highway Truck (South-West) */}
            <g
              id="node-transport-truck"
              transform="translate(345, 315)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Transport Corridor: Highway Container Logistics Fleet (Regional Stoppage on Southbound Route)'
                )
              }
              onMouseEnter={() => setHoveredNode('truck')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <circle
                r="26"
                fill="#081c2c"
                stroke="#06b6d4"
                strokeWidth="2"
                filter="url(#glowCyan)"
                className="group-hover:scale-110 transition-transform origin-center"
              />
              <circle
                r="21"
                fill="none"
                stroke="#06b6d4"
                strokeWidth="1"
                strokeDasharray="3,3"
                opacity="0.6"
              />
              <g transform="translate(-11, -10) scale(0.9)">
                <path
                  d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2M15 18H9M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14M17 14h5M7 18a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM17 18a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"
                  fill="none"
                  stroke="#22d3ee"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
              {hoveredNode === 'truck' && (
                <g transform="translate(0, -36)">
                  <rect
                    x="-65"
                    y="-16"
                    width="130"
                    height="20"
                    rx="5"
                    fill="#0f172a"
                    stroke="#06b6d4"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill="#22d3ee"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    Transport (Highway)
                  </text>
                </g>
              )}
            </g>

            {/* NODE 4: Cargo Transit Point (Above Transport) */}
            <g
              id="node-transit-point"
              transform="translate(395, 180)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Inland Freight Hub: Rail & Feeder Logistics Junction (Sortation Center)'
                )
              }
              onMouseEnter={() => setHoveredNode('transit')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <circle
                r="22"
                fill="#071828"
                stroke="#38bdf8"
                strokeWidth="1.8"
                filter="url(#glowCyan)"
                className="group-hover:scale-110 transition-transform origin-center"
              />
              <circle r="17" fill="none" stroke="#38bdf8" strokeWidth="0.8" opacity="0.6" />
              <g transform="translate(-9, -9) scale(0.75)">
                <path
                  d="M16.5 9.4 7.55 4.24a1.78 1.78 0 0 0-2.5 1.55v12.42a1.78 1.78 0 0 0 2.5 1.55L16.5 14.6a1.78 1.78 0 0 0 0-3.2Z"
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </g>
            </g>

            {/* NODE 5: Air Freight Terminal (South / Indochina) */}
            <g
              id="node-air-freight"
              transform="translate(435, 365)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Air Freight: Expedited Air Cargo Terminal (Alternate Transit Corridor, Indochina)'
                )
              }
              onMouseEnter={() => setHoveredNode('air')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <circle
                r="26"
                fill="#071b36"
                stroke="#38bdf8"
                strokeWidth="2"
                filter="url(#glowCyan)"
                className="group-hover:scale-110 transition-transform origin-center"
              />
              <circle
                r="21"
                fill="none"
                stroke="#38bdf8"
                strokeWidth="1"
                strokeDasharray="3,3"
                opacity="0.6"
              />
              <g transform="translate(-10, -10) scale(0.85)">
                <path
                  d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2Z"
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
              {hoveredNode === 'air' && (
                <g transform="translate(0, -36)">
                  <rect
                    x="-60"
                    y="-16"
                    width="120"
                    height="20"
                    rx="5"
                    fill="#0f172a"
                    stroke="#38bdf8"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill="#38bdf8"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    Air Freight Hub
                  </text>
                </g>
              )}
            </g>

            {/* NODE 6: Warehouse Depot (Far South / Malaysia-Singapore) */}
            <g
              id="node-warehouse-depot"
              transform="translate(510, 420)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Regional Warehouse: Fulfillment Depot (Allocated Safety Stock Buffer: 500 RCU)'
                )
              }
              onMouseEnter={() => setHoveredNode('wh')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <circle
                r="26"
                fill="#1b0c2e"
                stroke="#a855f7"
                strokeWidth="2"
                filter="url(#glowPurple)"
                className="group-hover:scale-110 transition-transform origin-center"
              />
              <circle
                r="21"
                fill="none"
                stroke="#a855f7"
                strokeWidth="1"
                strokeDasharray="3,3"
                opacity="0.6"
              />
              <g transform="translate(-10, -10) scale(0.85)">
                <path
                  d="M22 8.35V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.35A2 2 0 0 1 3.26 6.5l8-3.2a2 2 0 0 1 1.48 0l8 3.2A2 2 0 0 1 22 8.35Z"
                  fill="none"
                  stroke="#c084fc"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
                <path d="M6 18h12M6 14h12" stroke="#c084fc" strokeWidth="2" strokeLinecap="round" />
              </g>
              {hoveredNode === 'wh' && (
                <g transform="translate(0, -36)">
                  <rect
                    x="-60"
                    y="-16"
                    width="120"
                    height="20"
                    rx="5"
                    fill="#0f172a"
                    stroke="#a855f7"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill="#c084fc"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    Warehouse (500 RCU)
                  </text>
                </g>
              )}
            </g>

            {/* NODE 7: Customer Consignee Destination (Southeast / Pacific Rim) */}
            <g
              id="node-customer-consignees"
              transform="translate(650, 420)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Customer Consignees: 3,169 Impacted Delivery Accounts across Pacific Rim'
                )
              }
              onMouseEnter={() => setHoveredNode('cust')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <circle
                r="26"
                fill="#240c24"
                stroke="#ec4899"
                strokeWidth="2"
                filter="url(#glowPurple)"
                className="group-hover:scale-110 transition-transform origin-center"
              />
              <circle
                r="21"
                fill="none"
                stroke="#ec4899"
                strokeWidth="1"
                strokeDasharray="3,3"
                opacity="0.6"
              />
              <g transform="translate(-10, -10) scale(0.85)">
                <path
                  d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"
                  fill="none"
                  stroke="#f472b6"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
              {hoveredNode === 'cust' && (
                <g transform="translate(0, -36)">
                  <rect
                    x="-65"
                    y="-16"
                    width="130"
                    height="20"
                    rx="5"
                    fill="#0f172a"
                    stroke="#ec4899"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill="#f472b6"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    Customers (3,169)
                  </text>
                </g>
              )}
            </g>

            {/* NODE 8: Cargo Ship 1 (Northeast Pacific Maritime Shipping Lane) */}
            <g
              id="node-cargo-ship-1"
              transform="translate(700, 170)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Cargo Vessel 1: Trans-Pacific Maritime Container Ship (Anchored/Stalled outside East Asia harbor)'
                )
              }
              onMouseEnter={() => setHoveredNode('ship1')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <circle
                r="28"
                fill="#061e30"
                stroke="#06b6d4"
                strokeWidth="2.5"
                filter="url(#glowCyan)"
                className="group-hover:scale-110 transition-transform origin-center"
              />
              <circle
                r="23"
                fill="none"
                stroke="#06b6d4"
                strokeWidth="1"
                strokeDasharray="3,3"
                opacity="0.6"
              />
              <g transform="translate(-11, -11) scale(0.9)">
                <path
                  d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1 .6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1M19.38 20A11.6 11.6 0 0 0 21 14l-9-4-9 4c0 2.9.94 5.34 2.81 7.76M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6M12 10v4"
                  fill="none"
                  stroke="#22d3ee"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
              {hoveredNode === 'ship1' && (
                <g transform="translate(0, -36)">
                  <rect
                    x="-60"
                    y="-16"
                    width="120"
                    height="20"
                    rx="5"
                    fill="#0f172a"
                    stroke="#06b6d4"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill="#22d3ee"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    Cargo Vessel 1
                  </text>
                </g>
              )}
            </g>

            {/* NODE 9: Cargo Ship 2 (Central Pacific Maritime Shipping Lane) */}
            <g
              id="node-cargo-ship-2"
              transform="translate(670, 290)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  'Cargo Vessel 2: Feeder Line Container Carrier (Holding Anchorage in Philippine Sea)'
                )
              }
              onMouseEnter={() => setHoveredNode('ship2')}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <circle
                r="26"
                fill="#061e30"
                stroke="#06b6d4"
                strokeWidth="2"
                filter="url(#glowCyan)"
                className="group-hover:scale-110 transition-transform origin-center"
              />
              <circle
                r="21"
                fill="none"
                stroke="#06b6d4"
                strokeWidth="1"
                strokeDasharray="3,3"
                opacity="0.6"
              />
              <g transform="translate(-10, -10) scale(0.85)">
                <path
                  d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1 .6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1M19.38 20A11.6 11.6 0 0 0 21 14l-9-4-9 4c0 2.9.94 5.34 2.81 7.76M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6M12 10v4"
                  fill="none"
                  stroke="#22d3ee"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
              {hoveredNode === 'ship2' && (
                <g transform="translate(0, -36)">
                  <rect
                    x="-60"
                    y="-16"
                    width="120"
                    height="20"
                    rx="5"
                    fill="#0f172a"
                    stroke="#06b6d4"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill="#22d3ee"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    Cargo Vessel 2
                  </text>
                </g>
              )}
            </g>

            {/* ============================================================== */}
            {/* CENTRAL DISRUPTION RECTANGLE BADGE: EAST ASIA PORT             */}
            {/* ============================================================== */}
            <g
              id="central-disruption-badge"
              transform="translate(520, 240)"
              className="cursor-pointer group"
              onClick={() =>
                onSelectEntity?.(
                  `${eventName} (${eventId}): ${capacityLoss} Outage | Primary Disruption Epicenter impacting $1.33M gross exposure`
                )
              }
            >
              {/* Glowing Outer Badge Container */}
              <rect
                x="-88"
                y="-26"
                width="176"
                height="52"
                rx="10"
                fill="rgba(30, 8, 14, 0.94)"
                stroke="#ef4444"
                strokeWidth="2.5"
                filter="url(#glowRed)"
                className="group-hover:stroke-red-400 transition"
              />

              {/* Left Nautical Anchor Icon */}
              <g transform="translate(-72, -12)">
                <path
                  d="M12 2v20M5 12H2a10 10 0 0 0 20 0h-3M12 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>

              {/* Title Text: East Asia Port */}
              <text
                x="-38"
                y="-4"
                fill="#ffffff"
                fontSize="13"
                fontWeight="bold"
                fontFamily="sans-serif"
                letterSpacing="0.2px"
              >
                {eventName}
              </text>

              {/* Subtitle Badge: CLOSED (100%) */}
              <text
                x="-38"
                y="14"
                fill="#f87171"
                fontSize="11"
                fontWeight="bold"
                fontFamily="sans-serif"
                letterSpacing="0.3px"
              >
                CLOSED ({capacityLoss})
              </text>

              {/* Two small red indicator dots directly below the badge */}
              <circle cx="-16" cy="36" r="3.5" fill="#ef4444" filter="url(#glowRed)" />
              <circle cx="16" cy="36" r="3.5" fill="#ef4444" filter="url(#glowRed)" />
            </g>
          </g>
        </svg>
      </div>

      {/* ==================================================================== */}
      {/* 3. FIXED BOTTOM LEGEND (Exact match to reference screenshot)         */}
      {/* ==================================================================== */}
      <div className="pb-3 px-4 flex justify-center z-10 pointer-events-auto">
        <div className="bg-[#091526]/90 backdrop-blur-md border border-slate-700/60 rounded-xl px-4 sm:px-6 py-2 flex flex-wrap items-center justify-center gap-4 sm:gap-6 text-[11px] font-medium text-slate-300 shadow-md">
          <div className="flex items-center gap-1.5">
            <Anchor className="w-3.5 h-3.5 text-white" />
            <span>Port</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Factory className="w-3.5 h-3.5 text-amber-400" />
            <span>Factory</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Warehouse className="w-3.5 h-3.5 text-cyan-400" />
            <span>Warehouse</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Truck className="w-3.5 h-3.5 text-yellow-400" />
            <span>Transport</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Ship className="w-3.5 h-3.5 text-sky-400" />
            <span>Ship</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Plane className="w-3.5 h-3.5 text-blue-400" />
            <span>Air Freight</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-purple-400" />
            <span>Customer</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeographicShockwaveMap;

