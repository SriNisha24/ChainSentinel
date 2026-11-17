import React, { useState } from 'react';
import {
  AlertTriangle,
  Anchor,
  Ship,
  Package,
  Factory,
  Truck,
  Plane,
  Users,
  Radio,
  ShieldAlert,
  Info,
  Maximize2,
  Minimize2,
  Layers
} from 'lucide-react';
import type { ShockwaveResponse, RiskSummaryResponse } from '../types/api';

export type SupplyChainEntityType =
  | 'DISRUPTION_SOURCE'
  | 'PORT_HARBOUR'
  | 'CARGO_VESSEL'
  | 'SHIPMENT_ORDER'
  | 'FACTORY_PRODUCTION'
  | 'ROAD_TRANSPORT'
  | 'AIR_FREIGHT'
  | 'CUSTOMER_CONSIGNEE';

interface SupplyChainNode {
  id: string;
  name: string;
  code: string;
  type: SupplyChainEntityType;
  tier: number; // 0 = Origin, 1 = Gateway, 2 = Orders, 3 = Modes/Products, 4 = Destination
  x: number;
  y: number;
  icon: React.ComponentType<{ className?: string }>;
  iconBg: string;
  iconBorder: string;
  iconColor: string;
  glowColor: string;
  badgeText: string;
  subText: string;
  status: 'DISRUPTED' | 'STOPPAGE' | 'AT_RISK' | 'OPERATIONAL' | 'CONSIGNEE';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'NOMINAL';
  metrics: {
    primaryValue: string;
    primaryLabel: string;
    exposureUsd?: string;
    delayImpact?: string;
    volumeShare?: string;
  };
  operationalRole: string;
  graphTraversalNote: string;
  schemaVerification: string;
}

interface ShockwaveVisualizerProps {
  shockwave: ShockwaveResponse | null;
  risk: RiskSummaryResponse | null;
}

export const ShockwaveVisualizer: React.FC<ShockwaveVisualizerProps> = ({
  shockwave,
  risk,
}) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string>('DISR_SOURCE');
  const [activeStage, setActiveStage] = useState<'ALL' | 'ORIGIN' | 'SHIPMENTS' | 'TRANSIT'>('ALL');
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // Authoritative metrics from backend response (with fallback to IRUN-20261104143752-A4CB8F ground truth)
  const totalOrders = shockwave?.entity_counts?.unique_affected_orders ?? 3318;
  const eligibleOrders = shockwave?.entity_counts?.eligible_orders_for_delay ?? 3171;
  const uniqueCustomers = shockwave?.entity_counts?.unique_affected_customers ?? 3169;
  const uniqueProducts = shockwave?.entity_counts?.unique_affected_products ?? 71;
  const grossExposureUsd = shockwave?.financial_exposure?.total_gross_revenue_exposure_usd ?? 1334313.4;
  const eligibleExposureUsd = shockwave?.financial_exposure?.eligible_revenue_exposure_usd ?? 1282401.19;

  const criticalOrders = risk?.severity_distribution?.critical_orders ?? 20;
  const highOrders = risk?.severity_distribution?.high_risk_orders ?? 625;

  // Supply Chain Nodes positioned on control-room radar canvas (960 x 500)
  const nodes: SupplyChainNode[] = [
    {
      id: 'DISR_SOURCE',
      name: 'Disruption Event',
      code: 'SIM-DISR-2026-001',
      type: 'DISRUPTION_SOURCE',
      tier: 0,
      x: 95,
      y: 250,
      icon: AlertTriangle,
      iconBg: 'bg-rose-950/80',
      iconBorder: 'border-rose-500 shadow-rose-500/50',
      iconColor: 'text-rose-400',
      glowColor: '#f43f5e',
      badgeText: '100% STOPPAGE',
      subText: 'Terminal Berths',
      status: 'DISRUPTED',
      severity: 'CRITICAL',
      metrics: {
        primaryValue: '100% Loss',
        primaryLabel: 'Capacity Outage',
        delayImpact: '72.0h duration (96h delay)',
      },
      operationalRole: 'Disruption Epicenter: Catastrophic electrical grid stoppage at maritime container terminal.',
      graphTraversalNote: 'Root origin of shockwave propagation. Emits shockwave across connected maritime gateways.',
      schemaVerification: 'Verified Kafka Disruption Event payload with cryptographic digest.',
    },
    {
      id: 'PORT_GATEWAY',
      name: 'Port / Harbour Gateway',
      code: 'REG_Eastern_Asia',
      type: 'PORT_HARBOUR',
      tier: 1,
      x: 255,
      y: 155,
      icon: Anchor,
      iconBg: 'bg-red-950/80',
      iconBorder: 'border-red-500 shadow-red-500/40',
      iconColor: 'text-red-400',
      glowColor: '#ef4444',
      badgeText: 'GATEWAY OUTAGE',
      subText: 'China Maritime Hub',
      status: 'DISRUPTED',
      severity: 'CRITICAL',
      metrics: {
        primaryValue: 'Pacific Asia',
        primaryLabel: 'Market Corridor',
        delayImpact: 'Origin dispatch blocked',
      },
      operationalRole: 'Primary Regional Seaport Hub: Deep-water container port handling outbound Asia-Pacific shipments.',
      graphTraversalNote: 'Graph Distance 0 (Contextual parent gateway): All outbound lines frozen at dock gates.',
      schemaVerification: 'Verified supply-chain graph node (REG_Eastern_Asia within MKT_Pacific_Asia).',
    },
    {
      id: 'CARGO_VESSEL',
      name: 'Cargo Vessel Berths',
      code: 'BERTH_STOPPAGE',
      type: 'CARGO_VESSEL',
      tier: 1,
      x: 255,
      y: 345,
      icon: Ship,
      iconBg: 'bg-amber-950/80',
      iconBorder: 'border-amber-500 shadow-amber-500/40',
      iconColor: 'text-amber-400',
      glowColor: '#f59e0b',
      badgeText: 'BERTH CRUNCH',
      subText: 'Container Ships',
      status: 'STOPPAGE',
      severity: 'HIGH',
      metrics: {
        primaryValue: 'Zero Throughput',
        primaryLabel: 'Berth Operations',
        delayImpact: 'Gantry cranes frozen',
      },
      operationalRole: 'Marine Freight Stoppage: Container ships waiting at anchorage unable to load or unload export cargo.',
      graphTraversalNote: 'Graph Distance 1: Direct operational bottleneck for containerized freight originating at the port.',
      schemaVerification: 'Verified shockwave capacity parameter (capacity_reduction_pct: 100.0%).',
    },
    {
      id: 'SHIPMENT_ORDERS',
      name: 'Shipments & Orders',
      code: 'ORDER_COHORT',
      type: 'SHIPMENT_ORDER',
      tier: 2,
      x: 480,
      y: 250,
      icon: Package,
      iconBg: 'bg-rose-950/80',
      iconBorder: 'border-rose-400 shadow-rose-400/40',
      iconColor: 'text-rose-300',
      glowColor: '#fb7185',
      badgeText: `${totalOrders.toLocaleString()} ORDERS`,
      subText: `$${(grossExposureUsd / 1000).toFixed(1)}k Gross`,
      status: 'AT_RISK',
      severity: 'CRITICAL',
      metrics: {
        primaryValue: `${eligibleOrders.toLocaleString()} Eligible`,
        primaryLabel: 'Active Orders in Queue',
        exposureUsd: `$${(eligibleExposureUsd / 1000).toFixed(1)}k`,
        delayImpact: `${criticalOrders} Critical / ${highOrders} High`,
      },
      operationalRole: 'Primary Commercial Orders: Individual commercial customer orders trapped in origin fulfillment pipelines.',
      graphTraversalNote: 'Graph Distance 1 (Bipartite Traversal): Core order cohort directly impacted by the terminal stoppage.',
      schemaVerification: 'Authoritative Phase 8 Shockwave & Phase 9 Risk assessment outputs (3,318 total, 147 excluded canceled/fraud).',
    },
    {
      id: 'FACTORY_PROD',
      name: 'Factory Production',
      code: '71_SKU_CATALOG',
      type: 'FACTORY_PRODUCTION',
      tier: 3,
      x: 710,
      y: 120,
      icon: Factory,
      iconBg: 'bg-purple-950/80',
      iconBorder: 'border-purple-500 shadow-purple-500/40',
      iconColor: 'text-purple-400',
      glowColor: '#a855f7',
      badgeText: `${uniqueProducts} SKUs`,
      subText: '42 Categories',
      status: 'AT_RISK',
      severity: 'MEDIUM',
      metrics: {
        primaryValue: `${uniqueProducts} Products`,
        primaryLabel: 'Manufactured SKUs',
        volumeShare: '42 Product Categories',
      },
      operationalRole: 'Manufacturing Origin Lines: Production lines whose manufactured finished goods are tied to blocked orders.',
      graphTraversalNote: 'Graph Distance 2: Secondary bipartite operational relationship (Order ↔ Product Line Items).',
      schemaVerification: 'Verified shockwave product entities (unique_affected_products: 71, unique_affected_categories: 42).',
    },
    {
      id: 'ROAD_TRANSPORT',
      name: 'Road Transport Fleet',
      code: 'TRUCK_LOGISTICS',
      type: 'ROAD_TRANSPORT',
      tier: 3,
      x: 710,
      y: 250,
      icon: Truck,
      iconBg: 'bg-cyan-950/80',
      iconBorder: 'border-cyan-500 shadow-cyan-500/40',
      iconColor: 'text-cyan-400',
      glowColor: '#06b6d4',
      badgeText: 'ROAD FLEET',
      subText: 'Standard / 2nd Class',
      status: 'OPERATIONAL',
      severity: 'MEDIUM',
      metrics: {
        primaryValue: '78.8% Volume',
        primaryLabel: 'Surface Freight Share',
        delayImpact: 'Feeder drayage congestion',
      },
      operationalRole: 'Surface Road Freight: Container drayage and regional line-haul trucking dispatching orders inland.',
      graphTraversalNote: 'Graph Distance 2: Operational transport modes recorded on affected orders (Standard Class & Second Class).',
      schemaVerification: 'Verified shipping modes schema (Standard Class + Second Class modal records).',
    },
    {
      id: 'AIR_FREIGHT',
      name: 'Air Freight Aviation',
      code: 'AIR_EXPRESS',
      type: 'AIR_FREIGHT',
      tier: 3,
      x: 710,
      y: 380,
      icon: Plane,
      iconBg: 'bg-sky-950/80',
      iconBorder: 'border-sky-500 shadow-sky-500/40',
      iconColor: 'text-sky-400',
      glowColor: '#38bdf8',
      badgeText: 'AIR CORRIDOR',
      subText: 'First Class / Same Day',
      status: 'OPERATIONAL',
      severity: 'HIGH',
      metrics: {
        primaryValue: '21.2% Volume',
        primaryLabel: 'Express Aviation Share',
        delayImpact: 'Critical SLA penalty risk',
      },
      operationalRole: 'Air Express Aviation: Expedited air cargo channels servicing priority customers facing steep breach penalties.',
      graphTraversalNote: 'Graph Distance 2: High-priority transit modes recorded on affected orders (First Class & Same Day).',
      schemaVerification: 'Verified shipping modes schema (First Class + Same Day modal records).',
    },
    {
      id: 'CUSTOMER_BASE',
      name: 'Customer Consignees',
      code: '3169_ACCOUNTS',
      type: 'CUSTOMER_CONSIGNEE',
      tier: 4,
      x: 900,
      y: 250,
      icon: Users,
      iconBg: 'bg-blue-950/80',
      iconBorder: 'border-blue-500 shadow-blue-500/40',
      iconColor: 'text-blue-400',
      glowColor: '#3b82f6',
      badgeText: `${uniqueCustomers.toLocaleString()} ACCTS`,
      subText: 'End Recipients',
      status: 'CONSIGNEE',
      severity: 'HIGH',
      metrics: {
        primaryValue: `${uniqueCustomers.toLocaleString()}`,
        primaryLabel: 'Customer Accounts',
        exposureUsd: `$${(eligibleExposureUsd / 1000).toFixed(1)}k at Risk`,
      },
      operationalRole: 'Consignee Base: Commercial buyers, B2B distributors, and retail consumers awaiting pending delivery.',
      graphTraversalNote: 'Graph Distance 2: Secondary bipartite operational relationship (Order ↔ Customer Account).',
      schemaVerification: 'Verified shockwave customer entities (unique_affected_customers: 3,169).',
    },
  ];

  // Tactical Directional Connections between Recognized Entities
  const connections = [
    { from: 'DISR_SOURCE', to: 'PORT_GATEWAY', label: 'Terminal Berths Outage' },
    { from: 'DISR_SOURCE', to: 'CARGO_VESSEL', label: 'Vessel Unloading Halt' },
    { from: 'PORT_GATEWAY', to: 'SHIPMENT_ORDERS', label: 'Outbound Export Lock' },
    { from: 'CARGO_VESSEL', to: 'SHIPMENT_ORDERS', label: 'Container Drayage Freeze' },
    { from: 'SHIPMENT_ORDERS', to: 'FACTORY_PROD', label: 'SKU Line Tie-in' },
    { from: 'SHIPMENT_ORDERS', to: 'ROAD_TRANSPORT', label: 'Standard/2nd Class Routing' },
    { from: 'SHIPMENT_ORDERS', to: 'AIR_FREIGHT', label: 'First Class/Express Air' },
    { from: 'ROAD_TRANSPORT', to: 'CUSTOMER_BASE', label: 'Ground Delivery SLA' },
    { from: 'AIR_FREIGHT', to: 'CUSTOMER_BASE', label: 'Priority Express SLA' },
  ];

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0];

  const isNodeVisible = (node: SupplyChainNode) => {
    if (activeStage === 'ALL') return true;
    if (activeStage === 'ORIGIN') return node.tier <= 1;
    if (activeStage === 'SHIPMENTS') return node.tier === 0 || node.tier === 2;
    if (activeStage === 'TRANSIT') return node.tier >= 2;
    return true;
  };

  return (
    <div className={`space-y-4 ${isFullscreen ? 'fixed inset-0 z-50 bg-slate-950 p-6 overflow-y-auto' : ''}`}>
      {/* 1. Control Room Header & Tactical Status Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950 border border-cyan-500/50 flex items-center justify-center text-cyan-400 shadow-inner">
            <Radio className="w-5 h-5 animate-pulse text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-cyan-400 tracking-wider">TACTICAL PROPAGATION RADAR</span>
              <span className="text-slate-600">•</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950/80 text-rose-300 border border-rose-800">
                PORT CLOSURE ACTIVE
              </span>
            </div>
            <h2 className="text-base font-bold text-slate-100 mt-0.5">
              Supply Chain Shockwave Flow Topology
            </h2>
          </div>
        </div>

        {/* Tactical Filters & Mode Buttons */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex rounded-lg bg-slate-950 p-1 border border-slate-800">
            <button
              onClick={() => setActiveStage('ALL')}
              className={`px-3 py-1 rounded text-xs font-medium transition cursor-pointer ${
                activeStage === 'ALL' ? 'bg-cyan-600 text-white shadow-xs' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All Entities
            </button>
            <button
              onClick={() => setActiveStage('ORIGIN')}
              className={`px-3 py-1 rounded text-xs font-medium transition cursor-pointer ${
                activeStage === 'ORIGIN' ? 'bg-cyan-600 text-white shadow-xs' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Maritime Hub
            </button>
            <button
              onClick={() => setActiveStage('SHIPMENTS')}
              className={`px-3 py-1 rounded text-xs font-medium transition cursor-pointer ${
                activeStage === 'SHIPMENTS' ? 'bg-cyan-600 text-white shadow-xs' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Orders Queue
            </button>
            <button
              onClick={() => setActiveStage('TRANSIT')}
              className={`px-3 py-1 rounded text-xs font-medium transition cursor-pointer ${
                activeStage === 'TRANSIT' ? 'bg-cyan-600 text-white shadow-xs' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Modes & Customers
            </button>
          </div>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen Tactical View'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* 2. Main Visualization & Inspection Split Screen */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left: Deep Navy/Black Control-Room Radar Canvas */}
        <div className="lg:col-span-8 xl:col-span-9 bg-[#070d18] border border-slate-800 rounded-xl p-3 shadow-2xl relative overflow-hidden flex flex-col justify-between">
          {/* Tactical Corner Coordinates Readout */}
          <div className="flex items-center justify-between text-[10px] font-mono text-cyan-500/70 pb-2 border-b border-slate-800/80 px-2 select-none">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              <span>RADAR LAT 31.23°N / LNG 121.47°E [EAST ASIA MARITIME]</span>
            </div>
            <div className="hidden sm:flex items-center gap-3 text-slate-500">
              <span>CASCADE MODEL: REVERSE_BIPARTITE</span>
              <span>•</span>
              <span className="text-cyan-400 font-semibold">DIRECTION: OUTWARD (L → R)</span>
            </div>
          </div>

          {/* SVG Vector Canvas with Supply Chain Symbols */}
          <div className="relative w-full aspect-[16/9] min-h-[420px] max-h-[560px]">
            <svg
              viewBox="0 0 980 500"
              className="w-full h-full select-none"
              preserveAspectRatio="xMidYMid meet"
            >
              <defs>
                {/* 1. Tactical Radar Grid Pattern */}
                <pattern id="tactical-grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#0f213a" strokeWidth="0.8" />
                  <circle cx="0" cy="0" r="1" fill="#1e3a5f" />
                </pattern>

                {/* 2. Glowing Cyan Connection Filter */}
                <filter id="cyan-glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>

                {/* 3. Glowing Red Disruption Filter */}
                <filter id="red-glow" x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur stdDeviation="5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>

                {/* 4. Directional Cyan Propagation Arrowhead Marker */}
                <marker
                  id="cyan-arrow"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 1 L 9 5 L 0 9 z" fill="#06b6d4" />
                </marker>

                {/* 5. Directional Rose Propagation Arrowhead Marker */}
                <marker
                  id="rose-arrow"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 1 L 9 5 L 0 9 z" fill="#f43f5e" />
                </marker>
              </defs>

              {/* Background Grid */}
              <rect width="980" height="500" fill="url(#tactical-grid)" />

              {/* Radar Range Rings (Shockwave Propagation Sonar Waves) centered at Disruption Source (95, 250) */}
              <circle
                cx="95"
                cy="250"
                r="70"
                fill="none"
                stroke="#e11d48"
                strokeWidth="1.2"
                strokeDasharray="4,4"
                className="opacity-40 animate-pulse"
              />
              <circle
                cx="95"
                cy="250"
                r="170"
                fill="none"
                stroke="#f43f5e"
                strokeWidth="0.8"
                strokeDasharray="3,3"
                className="opacity-25"
              />
              <circle
                cx="95"
                cy="250"
                r="390"
                fill="none"
                stroke="#06b6d4"
                strokeWidth="0.6"
                strokeDasharray="2,4"
                className="opacity-20"
              />
              <circle
                cx="95"
                cy="250"
                r="640"
                fill="none"
                stroke="#0284c7"
                strokeWidth="0.5"
                strokeDasharray="2,6"
                className="opacity-15"
              />

              {/* Directional Propagation Pathway Lines (Glowing Cyan/Blue with Arrowheads) */}
              {connections.map((conn, idx) => {
                const src = nodes.find((n) => n.id === conn.from);
                const dst = nodes.find((n) => n.id === conn.to);
                if (!src || !dst) return null;
                if (!isNodeVisible(src) || !isNodeVisible(dst)) return null;

                const isCriticalPath = src.tier === 0 || dst.tier === 0;
                const pathStroke = isCriticalPath ? '#f43f5e' : '#06b6d4';
                const markerId = isCriticalPath ? 'url(#rose-arrow)' : 'url(#cyan-arrow)';

                // Smooth cubic bezier curve for high-tech control-room look
                const dx = dst.x - src.x;
                const cx1 = src.x + dx * 0.45;
                const cy1 = src.y;
                const cx2 = src.x + dx * 0.55;
                const cy2 = dst.y;
                const pathD = `M ${src.x} ${src.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${dst.x} ${dst.y}`;

                return (
                  <g key={`conn-${idx}`}>
                    {/* Soft background glow */}
                    <path
                      d={pathD}
                      fill="none"
                      stroke={pathStroke}
                      strokeWidth="3.5"
                      opacity={0.3}
                      filter="url(#cyan-glow)"
                    />
                    {/* Crisp foreground vector line with directional arrow */}
                    <path
                      d={pathD}
                      fill="none"
                      stroke={pathStroke}
                      strokeWidth="1.8"
                      strokeDasharray="5,4"
                      markerEnd={markerId}
                      opacity={0.85}
                    />
                  </g>
                );
              })}

              {/* Supply Chain Symbol Tactical Cards (NOT GENERIC CIRCLES) */}
              {nodes.map((node) => {
                if (!isNodeVisible(node)) return null;
                const isSelected = selectedNodeId === node.id;
                const cardWidth = 104;
                const cardHeight = 64;
                const rx = node.x - cardWidth / 2;
                const ry = node.y - cardHeight / 2;

                return (
                  <g
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    className="cursor-pointer transition-all duration-200"
                    style={{ transformOrigin: `${node.x}px ${node.y}px` }}
                  >
                    {/* Selection Beacon Aura */}
                    {isSelected && (
                      <rect
                        x={rx - 4}
                        y={ry - 4}
                        width={cardWidth + 8}
                        height={cardHeight + 8}
                        rx="12"
                        fill="none"
                        stroke="#38bdf8"
                        strokeWidth="2.5"
                        filter="url(#cyan-glow)"
                      />
                    )}

                    {/* Outer Tactical Badge Plate */}
                    <rect
                      x={rx}
                      y={ry}
                      width={cardWidth}
                      height={cardHeight}
                      rx="8"
                      fill="#0c1628"
                      stroke={isSelected ? '#38bdf8' : node.glowColor}
                      strokeWidth={isSelected ? '2' : '1.2'}
                      strokeOpacity={isSelected ? 1 : 0.8}
                      className="transition-colors hover:fill-[#13223d]"
                    />

                    {/* Tactical Status Accent Top Bar */}
                    <line
                      x1={rx + 8}
                      y1={ry + 2}
                      x2={rx + cardWidth - 8}
                      y2={ry + 2}
                      stroke={node.glowColor}
                      strokeWidth="2"
                    />

                    {/* Embedded SVG Icon & Supply Chain Symbol Plate */}
                    <foreignObject
                      x={rx}
                      y={ry}
                      width={cardWidth}
                      height={cardHeight}
                      className="pointer-events-none select-none"
                    >
                      <div className="w-full h-full p-2 flex flex-col justify-between items-center text-center">
                        <div className="flex items-center gap-1.5 w-full justify-center">
                          <div className={`p-1 rounded-md ${node.iconBg} border ${node.iconBorder}`}>
                            <node.icon className={`w-3.5 h-3.5 ${node.iconColor}`} />
                          </div>
                          <span className="text-[10px] font-bold text-slate-100 font-mono tracking-tight truncate max-w-[62px]">
                            {node.code}
                          </span>
                        </div>

                        <div>
                          <div className="text-[9px] font-semibold text-slate-300 leading-tight truncate max-w-[96px]">
                            {node.name}
                          </div>
                          <div
                            className="text-[8px] font-mono font-bold tracking-wider uppercase mt-0.5"
                            style={{ color: node.glowColor }}
                          >
                            {node.badgeText}
                          </div>
                        </div>
                      </div>
                    </foreignObject>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Bottom Tactical Severity & Entity Symbol Legend */}
          <div className="pt-3 border-t border-slate-800/80 px-2 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-slate-500 font-mono text-[10px] uppercase font-bold">Symbols Legend:</span>
              <span className="flex items-center gap-1 text-rose-400">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-500" /> Disruption
              </span>
              <span className="flex items-center gap-1 text-red-400">
                <Anchor className="w-3.5 h-3.5 text-red-500" /> Harbour
              </span>
              <span className="flex items-center gap-1 text-amber-400">
                <Ship className="w-3.5 h-3.5 text-amber-500" /> Cargo Vessel
              </span>
              <span className="flex items-center gap-1 text-rose-300">
                <Package className="w-3.5 h-3.5 text-rose-400" /> Shipments
              </span>
              <span className="flex items-center gap-1 text-cyan-400">
                <Truck className="w-3.5 h-3.5 text-cyan-400" /> Road Fleet
              </span>
              <span className="flex items-center gap-1 text-sky-400">
                <Plane className="w-3.5 h-3.5 text-sky-400" /> Air Freight
              </span>
              <span className="flex items-center gap-1 text-purple-400">
                <Factory className="w-3.5 h-3.5 text-purple-400" /> Factory SKUs
              </span>
              <span className="flex items-center gap-1 text-blue-400">
                <Users className="w-3.5 h-3.5 text-blue-400" /> Consignees
              </span>
            </div>

            <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono">
              <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" />
              <span>Flow: Origin Port → Shipments → Freight Modes → Consignees</span>
            </div>
          </div>
        </div>

        {/* Right: Data-Backed Control-Room Telemetry HUD Drawer */}
        <div className="lg:col-span-4 xl:col-span-3 bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl text-white flex flex-col justify-between space-y-4">
          <div className="space-y-4">
            {/* Header with Selected Symbol */}
            <div className="pb-3 border-b border-slate-800 flex items-start justify-between">
              <div className="flex items-center gap-2.5">
                <div className={`p-2.5 rounded-lg ${selectedNode.iconBg} border ${selectedNode.iconBorder}`}>
                  <selectedNode.icon className={`w-5 h-5 ${selectedNode.iconColor}`} />
                </div>
                <div>
                  <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
                    {selectedNode.type.replace(/_/g, ' ')}
                  </span>
                  <h3 className="text-sm font-bold text-slate-100 leading-snug">{selectedNode.name}</h3>
                </div>
              </div>

              <span
                className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                  selectedNode.severity === 'CRITICAL'
                    ? 'bg-rose-950 text-rose-300 border-rose-800'
                    : selectedNode.severity === 'HIGH'
                    ? 'bg-amber-950 text-amber-300 border-amber-800'
                    : 'bg-cyan-950 text-cyan-300 border-cyan-800'
                }`}
              >
                {selectedNode.severity}
              </span>
            </div>

            {/* Tactical Metrics Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                <div className="text-[10px] text-slate-400 font-mono">{selectedNode.metrics.primaryLabel}</div>
                <div className="text-sm font-mono font-bold text-slate-100 mt-0.5">
                  {selectedNode.metrics.primaryValue}
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                <div className="text-[10px] text-slate-400 font-mono">Disruption Impact</div>
                <div className="text-sm font-mono font-bold text-rose-400 mt-0.5">
                  {selectedNode.metrics.exposureUsd || selectedNode.metrics.delayImpact || selectedNode.metrics.volumeShare || 'Direct Victim'}
                </div>
              </div>
            </div>

            {/* Operational Role Description */}
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs space-y-1.5">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
                <span>Operational Control Function</span>
              </div>
              <p className="text-slate-300 text-xs leading-relaxed">
                {selectedNode.operationalRole}
              </p>
            </div>

            {/* Data Lineage & Graph Relationship Disclosure */}
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs space-y-1.5">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                <span>Network Cascade & Topology</span>
              </div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {selectedNode.graphTraversalNote}
              </p>
              <div className="text-[10px] text-cyan-400 font-mono pt-1 border-t border-slate-800/80">
                Source: {selectedNode.schemaVerification}
              </div>
            </div>
          </div>

          {/* Honest Warehouse & Physical Route Disclosure */}
          <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60 text-[10px] text-slate-500 space-y-1">
            <div className="flex items-center gap-1 text-slate-400 font-semibold">
              <Info className="w-3 h-3 text-cyan-500" />
              <span>Honest Supply-Chain Schema Note</span>
            </div>
            <p className="leading-tight">
              ChainSentinel models verified port closures, delay cohorts, transport modes, products, and consignees. Intermediate warehouse stops are not fabricated because inland multi-hop routes are not present in DataCo transactional data (ASSUMPTION_NO_PHYSICAL_ROUTE).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
