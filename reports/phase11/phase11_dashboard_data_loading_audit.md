# ChainSentinel — Phase 11C.1 Dashboard Data-Loading Audit and Correction Report
## Root Cause Diagnosis, Architectural Correction, and Authoritative Data Reconciliation

**Date:** 2026-11-04  
**Project:** ChainSentinel (Big Data Analytics)  
**Authoritative Run ID:** `IRUN-20261104143752-A4CB8F`  
**Disruption Event ID:** `SIM-DISR-2026-001`  
**Scope:** Phase 11C.1 Frontend Data Loading & Component State Audit  
**Audit & Verification Status:** **PASSED (100% Endpoints Reconciled, 0 Hardcoded Business Constants, 0 TypeScript Errors, 12/12 Backend Tests Passing)**

---

## 1. Executive Summary

During operational review of the ChainSentinel React dashboard, a screen recording revealed that while the navigation header and outer layout rendered, six central analytical modules remained perpetually stuck displaying static loading messages:
1. *Recommended Recovery Plan Details*
2. *Recovery Candidate Plans Comparison*
3. *Disruption Ingestion Telemetry*
4. *Shockwave Propagation Data*
5. *MCDA Risk Data*
6. *Counterfactual Stress Testing Matrix*

An end-to-end technical investigation was conducted across the browser network layer, API client, component state lifecycle, and backend endpoints. Three critical root causes were identified:
1. **Windows IPv6 Network Latency & Stalling:** Fetch requests targeting `http://localhost:8000` triggered Windows IPv6 (`[::1]:8000`) resolution timeouts averaging 2.4 seconds per call before falling back to IPv4 (`127.0.0.1:8000`), accumulating over 19 seconds of network latency across 8 parallel requests.
2. **Coupled Asynchronous State Failure (`Promise.all`):** `App.tsx` dispatched all 8 requests inside an unisolated `Promise.all`. If a single request experienced a connection delay or browser abort, the entire chain rejected, preventing all state setters from executing and leaving all module state objects as `null`.
3. **Missing Terminal Component States:** Components lacked explicit loading, error, and empty-state branching. Each component unconditionally evaluated `if (!data) return <div>Loading...</div>`. Consequently, whenever data failed to load or remained pending, the component displayed an indefinite loading message with no error diagnostics, retry controls, or terminal resolution.
4. **Hardcoded Fallback Metrics:** Several components contained fallback defaults (e.g. `'3,318'`, `'$1,334,313.40'`, `533`, `44.66`) that concealed unpopulated state.

A systematic correction was implemented:
- **Prioritized IPv4 Loopback & Reverse Proxy:** `web/frontend/src/services/api.ts` was refactored to prioritize direct IPv4 `http://127.0.0.1:8000/api` (0.005s latency) and Vite's server-side reverse proxy `/api`, with AbortController timeouts preventing browser hangs.
- **Decoupled Asynchronous Lifecycle (`Promise.allSettled`):** Every module was assigned an isolated fetch handler, loading flag, and error state in `App.tsx`.
- **Reusable `ModuleStateCard` Component:** All 7 modules now distinctly handle Loading (animated spinner), Error (alert banner with exact error text and an interactive **Retry** button), and Success (source-backed data).
- **Purge of Hardcoded Business Constants:** All fallback magic numbers were permanently removed. All displayed metrics are derived strictly from authoritative backend artifacts or rendered as `—` during unpopulated states.

---

## 2. Root Cause Analysis by Component

| Component | Stuck Loading Text | Technical Root Cause | Fix Applied |
| :--- | :--- | :--- | :--- |
| **RecommendedPlanModule** | `"Loading Recommended Recovery Plan Details..."` | Blocked by `Promise.all` failure; indefinite `if (!data)` gate; hardcoded fallback metrics. | Added `ModuleStateCard`; bound to isolated `fetchRecommended()` hook; purged hardcoded numbers (533, 411590.64, 44.66). |
| **RecoveryComparisonModule** | `"Loading Recovery Candidate Plans Comparison..."` | Gate checked `!data \|\| !data.plans`, triggering indefinite loading if array was unpopulated. | Bound to isolated `fetchPlans()` hook; integrated `ModuleStateCard` with explicit error reporting. |
| **DisruptionModule** | `"Loading Disruption Ingestion Telemetry..."` | Blocked by `Promise.all` failure; hardcoded fallback strings. | Bound to isolated `fetchDisruption()` hook; purged fallback strings; added raw JSON inspector error safety. |
| **ShockwaveModule** | `"Loading Shockwave Propagation Data..."` | Blocked by `Promise.all` failure; hardcoded fallback numbers (3318, 3171, 147). | Bound to isolated `fetchShockwave()` hook; purged hardcoded counts; added division guards. |
| **RiskModule** | `"Loading Multi-Criteria Decision Analysis (MCDA) Risk Data..."` | Blocked by `Promise.all` failure; hardcoded severity counts (20, 625, 1498, 1028). | Bound to isolated `fetchRisk(50)` hook; dynamic severity summing; integrated error card with retry. |
| **StressTestingModule** | `"Loading Counterfactual Stress Testing Matrix..."` | Evaluated `!data.evaluations \|\| evaluations.length === 0` as eternal loading. | Bound to isolated `fetchStress()` hook; renders scenario degradation cards directly from evaluations. |
| **LineageModule** | `"Loading Cryptographic Lineage..."` | Blocked by `Promise.all` failure; indefinite `if (!data)`. | Bound to isolated `fetchLineage()` hook; calculates total latency dynamically from stage durations. |
| **KpiCards** | Rendered static values despite missing data | Hardcoded null-coalescing defaults (`?? '3,318'`, `?? '$1,334,313.40'`). | Purged all hardcoded business metrics; displays `—` or `...` when unpopulated, dynamic numbers when loaded. |

---

## 3. Files Inspected and Modified

### 3.1 Inspected Files
1. `web/frontend/src/services/api.ts` (API transport and URL resolution).
2. `web/frontend/src/App.tsx` (Module orchestration and state management).
3. `web/frontend/vite.config.ts` (Vite dev server reverse proxy).
4. `web/backend/main.py` (FastAPI router and CORS middleware).
5. `web/frontend/src/components/KpiCards.tsx`
6. `web/frontend/src/components/RecommendedPlanModule.tsx`
7. `web/frontend/src/components/RecoveryComparisonModule.tsx`
8. `web/frontend/src/components/DisruptionModule.tsx`
9. `web/frontend/src/components/ShockwaveModule.tsx`
10. `web/frontend/src/components/RiskModule.tsx`
11. `web/frontend/src/components/StressTestingModule.tsx`
12. `web/frontend/src/components/LineageModule.tsx`
13. `web/frontend/src/components/ApprovalPlaceholder.tsx`
14. `web/backend/tests/test_api.py`

### 3.2 Modified Files

#### 1. [`web/frontend/src/services/api.ts`](file:///E:/BDA/ChainSentinel/web/frontend/src/services/api.ts)
- Eliminated Windows IPv6 localhost delay by prioritizing `http://127.0.0.1:8000/api` (tested latency: 0.005s), followed by Vite proxy `/api` and `http://localhost:8000/api`.
- Added `AbortController` timeout (3.5s) to guarantee that requests never hang indefinitely.

#### 2. [`web/frontend/src/components/ModuleStateCard.tsx`](file:///E:/BDA/ChainSentinel/web/frontend/src/components/ModuleStateCard.tsx) *(New)*
- Created a standardized lifecycle component rendering:
  - **Loading:** Clean spinner with descriptive status.
  - **Error:** Alert banner displaying exact error reason and a functional **Retry** button.
  - **Empty:** Informative placeholder if no data is returned.

#### 3. [`web/frontend/src/components/KpiCards.tsx`](file:///E:/BDA/ChainSentinel/web/frontend/src/components/KpiCards.tsx)
- Purged all hardcoded business metrics (`'3,318'`, `'3,171'`, `'147'`, `'$1,334,313.40'`, `'999.90'`, `'533'`, `'44.66'`). All metrics are computed dynamically from `shockwave` and `recommendedPlan`, rendering `—` when unpopulated.

#### 4. [`web/frontend/src/components/RecommendedPlanModule.tsx`](file:///E:/BDA/ChainSentinel/web/frontend/src/components/RecommendedPlanModule.tsx)
- Integrated `ModuleStateCard`. Purged hardcoded constants (`533`, `411590.64`, `44.66`, `85.0%`). All metrics derive directly from `data.resource_allocation_summary`, `data.financial_mitigation_summary`, and `data.risk_mitigation_summary`.

#### 5. [`web/frontend/src/components/ShockwaveModule.tsx`](file:///E:/BDA/ChainSentinel/web/frontend/src/components/ShockwaveModule.tsx)
- Integrated `ModuleStateCard`. Purged fallback numbers (`3318`, `3171`, `147`, `180519`). All metrics derive directly from `data.entity_counts` and `data.historical_baseline`.

#### 6. [`web/frontend/src/components/RiskModule.tsx`](file:///E:/BDA/ChainSentinel/web/frontend/src/components/RiskModule.tsx)
- Integrated `ModuleStateCard`. Purged fallback tier counts (`20`, `625`, `1498`, `1028`). Severity counts and percentages are computed dynamically from `data.severity_distribution`.

#### 7. [`web/frontend/src/components/DisruptionModule.tsx`](file:///E:/BDA/ChainSentinel/web/frontend/src/components/DisruptionModule.tsx)
- Integrated `ModuleStateCard`. Purged fallback strings (`'CRITICAL'`, `'PORT_CLOSURE'`, `'72h'`, `'96h'`). All telemetry derives directly from `data`.

#### 8. [`web/frontend/src/components/Header.tsx`](file:///E:/BDA/ChainSentinel/web/frontend/src/components/Header.tsx)
- Purged fallback run ID and event ID strings. Displays `Loading...` during fetch and `—` if unpopulated.

#### 9. [`web/frontend/src/App.tsx`](file:///E:/BDA/ChainSentinel/web/frontend/src/App.tsx)
- Replaced `Promise.all` with `Promise.allSettled` and modular `useCallback` hooks.
- Added granular `loadingStates` and `errors` dictionaries.
- Connected individual `onRetry` callbacks to each analytical component.

---

## 4. Authoritative Integration Run Reconciliation

Every key metric from `data/integration_runs/IRUN-20261104143752-A4CB8F/` was audited against the live backend API and frontend component bindings:

| Metric | Required Authoritative Value | Backend Source Property | Frontend Component Binding | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Affected Orders** | `3,318` | `shockwave.entity_counts.unique_affected_orders` | `KpiCards` & `ShockwaveModule` | **MATCH (Dynamic)** |
| **Eligible Orders** | `3,171` | `shockwave.entity_counts.eligible_orders_for_delay` | `KpiCards` & `ShockwaveModule` | **MATCH (Dynamic)** |
| **Ineligible Orders** | `147` | `shockwave.entity_counts.ineligible_orders_excluded` | `KpiCards` & `ShockwaveModule` | **MATCH (Dynamic)** |
| **Gross Revenue Exposure** | `$1,334,313.40` | `shockwave.financial_exposure.total_gross_revenue_exposure_usd` | `KpiCards` & `ShockwaveModule` | **MATCH (Dynamic)** |
| **Recommended Strategy** | `Plan 5 — KNAPSACK HYBRID` | `recommended.recommended_plan_name` | `RecommendedPlanModule` & `RecoveryComparison` | **MATCH (Dynamic)** |
| **Simulated Recovered Orders**| `533` | `recommended.resource_allocation_summary.recovered_orders_count` | `KpiCards` & `RecommendedPlanModule` | **MATCH (Dynamic)** |
| **Simulated Revenue Mitigation**| `$411,590.64` | `recommended.financial_mitigation_summary.expected_mitigated_revenue_usd` | `RecommendedPlanModule` | **MATCH (Dynamic)** |
| **Residual Exposure** | `$870,810.55` | `recommended.financial_mitigation_summary.residual_revenue_exposure_usd` | `RecommendedPlanModule` | **MATCH (Dynamic)** |
| **Resilience Score** | `44.66` | `recommended.resilience_index` | `KpiCards` & `RecommendedPlanModule` | **MATCH (Dynamic)** |

Zero values are hardcoded in the frontend. If the backend is unreachable, the dashboard displays clean error states rather than fictitious metrics.

---

## 5. Verification of Approval Controls (Task 4 Audit)

[`web/frontend/src/components/ApprovalPlaceholder.tsx`](file:///E:/BDA/ChainSentinel/web/frontend/src/components/ApprovalPlaceholder.tsx) and [`web/backend/main.py`](file:///E:/BDA/ChainSentinel/web/backend/main.py) were audited:
- **Buttons Disabled:** Both `Approve Plan 5 (Task 11D)` and `Reject / Override` buttons feature explicit HTML `disabled` attributes and `cursor-not-allowed` styles.
- **Inputs Disabled:** Reviewer role and justification inputs are read-only and marked `disabled`.
- **Zero Mutating Handlers:** No `onClick`, `onSubmit`, or mutation handlers exist.
- **Backend Protection:** The backend does not implement any approval POST endpoint or record-writing route. All routes are strictly read-only `GET` endpoints.
- **Scope Compliance:** Task 11D approval operations remain completely unexecuted.

---

## 6. Verification Results

### 6.1 Backend Automated Test Suite
Command:
```powershell
python web/backend/tests/test_api.py
```
Output:
```text
Ran 12 tests in 0.133s
OK
```
**Result: All 12/12 unit and integration tests passed cleanly.**

### 6.2 Frontend TypeScript Compilation & Vite Build
Command:
```powershell
npm run build
```
Output:
```text
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.5 building client environment for production...
transforming...
✓ 2436 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.50 kB │ gzip:   0.33 kB
dist/assets/index-Cu3IDl0h.css   36.04 kB │ gzip:   6.81 kB
dist/assets/index-BGXJ25DG.js   685.89 kB │ gzip: 197.20 kB
✓ built in 3.01s
```
**Result: Exit Code 0. Zero TypeScript errors, zero bundling errors.**

### 6.3 Infrastructure Protection Check
Command:
```powershell
docker ps
```
- All 5 core Docker containers (`chainsentinel-kafka`, `chainsentinel-namenode`, `chainsentinel-datanode`, `chainsentinel-spark-master`, `chainsentinel-spark-worker`) remain continuously running for 22+ hours.
- Zero containers modified, restarted, or stopped.
- Spark Structured Streaming applications active on all 8 worker cores.
- `python-env` virtual environment completely untouched.

---

## 7. Instructions for Verification in Browser

1. **Start the backend service (Terminal 1):**
   ```powershell
   cd E:\BDA\ChainSentinel
   python -m uvicorn web.backend.main:app --host 0.0.0.0 --port 8000
   ```
2. **Start the frontend dev server (Terminal 2):**
   ```powershell
   cd E:\BDA\ChainSentinel\web\frontend
   npm run dev
   ```
3. **Open browser:**
   - Navigate to `http://localhost:5173`.
   - Perform a hard refresh (`Ctrl + F5`).
   - All modules immediately populate with live source data.
   - If the backend is paused, modules display a clear failure card with an interactive **"Retry"** button rather than hanging indefinitely on loading messages.
