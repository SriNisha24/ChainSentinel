# ChainSentinel — Human-in-the-Loop Review Console (Frontend)

## 1. Overview
The **ChainSentinel Operational Review and Approval Console** is a modern React + TypeScript + Vite single-page application tailored for supply-chain operations managers and risk officers. It connects directly to the FastAPI backend to visualize real-time disruption telemetry, shockwave propagation, multi-criteria risk tiers, recovery strategy alternatives, counterfactual stress tests, and cryptographic provenance lineages.

> **Watermark Notice:**
> `SIMULATION & DECISION-SUPPORT PROTOTYPE — NO PHYSICAL DISPATCH EXECUTED`
> This frontend is strictly an analytical and decision-support interface. It does not trigger external carrier APIs or execute physical transportation maneuvers.

---

## 2. Technology Stack
- **Framework:** React 19 + TypeScript
- **Build Tool:** Vite 8 (Rolldown engine)
- **Styling:** Tailwind CSS + PostCSS
- **Visualizations:** Recharts (Bar, Line, and responsive containers)
- **Icons:** Lucide React
- **Design Aesthetic:** Mission-control dark navy palette (`#0b1120`, `#151e2e`, `#0f172a`)

---

## 3. Component Architecture
```
src/
├── types/
│   └── api.ts                    # TypeScript data contracts matching FastAPI Pydantic schemas
├── services/
│   └── api.ts                    # Strongly typed API client pointing to http://localhost:8000/api
├── components/
│   ├── Header.tsx                # Disruption badge, run ID, gate indicators, and prominent prototype banner
│   ├── KpiCards.tsx              # High-level metrics: 3,318 affected, $1.33M revenue, 999.90 RCU, 44.66 resilience
│   ├── DisruptionModule.tsx      # Phase 7 HDFS event details, epicenter coordinates, raw JSON inspector
│   ├── ShockwaveModule.tsx       # Phase 8 graph propagation, 3,171 eligible vs 147 ineligible breakdown
│   ├── RiskModule.tsx            # Phase 9 MCDA risk tiers (Critical: 20, High: 625), PII-masked priority review table
│   ├── RecoveryComparisonModule.tsx # Phase 10 candidate recovery plans trade-off bar chart and comparison matrix
│   ├── RecommendedPlanModule.tsx # Phase 10 Plan 5 deep-dive, 17/20 critical resolution, and RCU allocation sample
│   ├── StressTestingModule.tsx   # Phase 10 counterfactual stress tests (5 scenarios x 6 plans) resilience lines
│   ├── LineageModule.tsx         # Cryptographic execution trace across 4 stages with SHA-256 signatures
│   ├── ApprovalPlaceholder.tsx   # Task 11D operational review sign-off placeholder (actions safely inactive)
│   └── index.ts                  # Component barrel export
├── App.tsx                       # Tabbed and executive dashboard view, data fetching, error handling
├── main.tsx                      # React root entry point
└── index.css                     # Tailwind imports and dark scrollbar styles
```

---

## 4. How to Run

### Development Server
```powershell
cd E:\BDA\ChainSentinel\web\frontend
npm run dev
```
By default, the Vite dev server starts at `http://localhost:5173`. Ensure the FastAPI backend is running concurrently on port 8001:
```powershell
python -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8001
```

### Production Build
```powershell
cd E:\BDA\ChainSentinel\web\frontend
npm run build
```
Build outputs are generated in `dist/`.

### Preview Production Build
```powershell
cd E:\BDA\ChainSentinel\web\frontend
npm run preview
```
