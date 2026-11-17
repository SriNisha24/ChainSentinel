# CHAINSENTINEL — DATASET INTELLIGENCE FRONTEND IMPLEMENTATION REPORT
**Module:** Frontend Presentation, Interaction Layer & Multi-Workflow UI  
**Author:** ChainSentinel Engineering Agent  
**Environment:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons  
**Date:** November 2026  
**Status:** COMPLETE & PRODUCTION-READY (Build Verified)

---

## 1. Executive Summary

This report documents the design, architecture, and production delivery of the ChainSentinel user interface. The frontend transforms the operational dashboard into an enterprise supply-chain intelligence console that supports two independent, non-conflicting workflows:

1. **Workflow A (Dataset Intelligence):** Provides an interactive workflow for selecting the authoritative DataCo supply-chain dataset or uploading new compatible CSV datasets. It executes client-side schema compatibility profiling, 15-row data previews, single-click multi-model execution, historical run comparisons, and granular record-level inspection.
2. **Workflow B (Live Disruption Monitoring & Tactical Radar):** Provides real-time visibility into streaming disruptions injected via the Windows terminal pipeline (`generate_disruption_event.py` → Kafka `disruption-events` → Spark Structured Streaming → Hadoop HDFS). The interface features a dark control-room shockwave radar utilizing recognized supply-chain vector symbols (cargo ships, ports, warehouses, trucks, aircraft, factories, and shipments) rather than generic circular nodes.

All 9 primary operational views have been compiled, verified with TypeScript strict checking, and bundled via Vite with 0 errors.

---

## 2. Navigation Architecture & View Hierarchy

The frontend incorporates a persistent, collapsible sidebar supporting responsive mobile slide-out behavior and clean enterprise light aesthetics (white and slate palettes with professional blue accents):

| Tab Identifier | Screen Component | Primary Purpose & Key Features |
|---|---|---|
| `home` | `HomeScreen.tsx` | Operational snapshot, dual workflow launch cards, active streaming incident banner, pending approvals alert, and recent dataset analysis runs table. |
| `dataset_analysis` | `DatasetAnalysisScreen.tsx` | Dataset selection (DataCo 180k rows vs. CSV upload), feature profiling, model compatibility checklist, 15-row preview table with column filter, and execution trigger. |
| `analysis_results` | `AnalysisResultsScreen.tsx` | Multi-model analytical findings, historical run switcher (`ARUN-...`), 4 dedicated model tabs, and paginated underlying record inspection table. |
| `disruptions` | `DisruptionsScreen.tsx` | Workflow B terminal streaming status pipeline (5-stage ingestion tracker) and dark control-room SVG shockwave radar with recognized supply-chain symbols. |
| `recovery` | `RecoveryPlansScreen.tsx` | Bounded Knapsack multi-objective recovery recommendations, capacity constraint metrics (500 RCU limit), and counterfactual stress testing. |
| `approvals` | `ApprovalsScreen.tsx` | Human-in-the-loop operational review gate, decision submission form, and immutable JSON decision ledger. |
| `alerts` | `AlertsScreen.tsx` | Operational threshold alerts, risk severity filtering, and acknowledgement lifecycle management (Acknowledge, Resolve, Dismiss). |
| `models` | `ModelInsightsScreen.tsx` | Production model metadata, Population Stability Index (PSI) drift monitoring, user feedback logging, and isolated retraining candidate tracking. |
| `settings` | `SettingsScreen.tsx` | Security role-based access control (RBAC), defense-in-depth infrastructure verification, and live audit logging. |

---

## 3. Workflow A: Dataset Intelligence Implementation

### 3.1 Dataset Selection & Upload (`DatasetAnalysisScreen.tsx`)
- **Option A (Original DataCo):** Default pre-cataloged asset `DS-DATACO-ORIGINAL` (180,519 records, 53 columns, 172.5 MB). Provides instant validation without file re-uploading.
- **Option B (CSV Upload):** Modern drag-and-drop or file picker uploading to isolated storage (`data/datasets/uploaded/`). Enforces strict 120 MB file size validation and filename sanitization.
- **Feature Profiling & Compatibility Matrix:** Real-time feedback displaying:
  - Total records and columns.
  - Missing value counts and duplicate row counts.
  - Green/amber compatibility status badges across all 4 machine learning models.
- **Interactive Data Preview:** Paginated 15-row preview with a column search filter, displaying formatted currencies, dates, shipping modes, customer segments, and order statuses.
- **Execution Action:** Single-click "Start Multi-Model Analysis" button with animated progress indicator. Automatically transitions the operator to `AnalysisResultsScreen` upon completion.

### 3.2 Analytical Findings & Record Drill-Down (`AnalysisResultsScreen.tsx`)
- **Historical Run Switcher:** Dropdown selector populated via `/api/analysis/runs`, allowing instant inspection of historical runs (`ARUN-...`) and baseline comparisons without reloading.
- **Model Result Views:**
  1. **Delay Prediction Tab:** Displays mean delay probability (55.07%), high-risk order percentage (58.3%), and high-risk orders count.
  2. **Anomaly Detection Tab:** Displays statistical profit anomalies (2,216 flagged records, $1.15M at-risk loss), breakdown by negative profit thresholds, and cluster centroid distances.
  3. **Disruption What-If Tab:** Comparative cards for 4 pre-configured disruption scenarios (Port Congestion, Regional Stoppage, Demand Surge, Hurricane Alert) detailing expected delay additions and exposed values.
  4. **Demand Forecasting & Capacity Tab:** Daily moving average demand projection, SLA capacity ceiling (65 orders/day), 85% utilization threshold, and shortfall risk warning.
- **Drill-Down Underlying Records Table:**
  - Paginated table (10 records per page) with total count indicators and page navigation.
  - Search filter querying Order ID, Customer City, and Shipping Mode.
  - Dynamic table columns showing actual model predictions: Delay Probability, Statistical Anomaly Flag, Forecasted Daily Demand, and SLA Shortfall Risk.

---

## 4. Workflow B: Live Disruption Monitoring & Tactical Radar

### 4.1 Ingestion Pipeline Tracker (`DisruptionsScreen.tsx`)
A 5-stage live status pipeline tracking the end-to-end event lifecycle:
1. **Event Submitted:** Windows Terminal JSON generator (`generate_disruption_event.py`).
2. **Event Received:** Apache Kafka Broker (`disruption-events` topic).
3. **Event Consumed:** Spark Structured Streaming Engine (`streaming_disruption_processor.py`).
4. **Event Persisted:** Hadoop HDFS Storage (`/chainsentinel/disruptions/`).
5. **Event Analysed:** NetworkX Shockwave Radar & Recovery Engine.

### 4.2 Tactical SVG Shockwave Radar (`ShockwaveVisualizer.tsx`)
- **Visual Design:** Deep slate/navy background (`#0b1120`) providing a high-contrast tactical operations center aesthetic.
- **Recognizable Supply-Chain Symbols:** Completely eliminates generic circular nodes in favor of dedicated vector icons:
  - **Port / Harbour:** Crane and berth icon for maritime terminals.
  - **Cargo Ship:** Ocean vessel icon for maritime transit routes.
  - **Warehouse / DC:** Logistics depot icon for storage facilities.
  - **Factory:** Manufacturing plant icon with smokestacks.
  - **Truck / Transport:** Highway transport vehicle icon for road logistics.
  - **Aircraft:** Cargo jet icon for expedited air freight.
  - **Shipment / Package:** Carton box icon for individual customer consignments.
  - **Customer:** Retail consumer/store icon for terminal delivery nodes.
  - **Disruption Epicenter:** Pulsing red/orange hazard warning beacon indicating the origin point.
- **Dynamic Interaction:** Interactive node selection revealing full entity metadata, tier depth, delay impact, and criticality ratings.

---

## 5. Verification & Build Confirmation

The frontend codebase was compiled using TypeScript and Vite:

```bash
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.5 building client environment for production...
transforming...
2064 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.50 kB │ gzip:   0.33 kB
dist/assets/index-CzBuwXoQ.css   68.31 kB │ gzip:  11.47 kB
dist/assets/index-DgJ69FrU.js   386.70 kB │ gzip: 105.23 kB
built in 6.02s
```

- **TypeScript Compilation:** 0 errors, 0 warnings under strict checking.
- **Asset Generation:** Full production bundle generated in `web/frontend/dist/`.
- **API Connectivity:** Standardized on `http://localhost:8000/api` with fallback error banners.

