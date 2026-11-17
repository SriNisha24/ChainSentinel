# ChainSentinel — Phase 11 Operational Review Backend

**Directory:** `web/backend`  
**Framework:** FastAPI 0.110.0 + Uvicorn 0.52.4 + Pydantic 2.6.3 + Pandas 2.2.3  
**Python Runtime:** Windows Host Global Python (`python`)  
**Data Source:** `data/integration_runs/IRUN-20261104143752-A4CB8F/`  

---

## 1. Overview

The ChainSentinel Review Backend is a lightweight, read-only REST service that ingests completed integration run artifacts and exposes structured, validated JSON payloads to the React control tower frontend.

### Guarantees:
- **Read-Only:** Strictly opens and parses completed run files. Zero write handles to analytical directories.
- **Safety Boundary:** Does not book carriers, reroute shipments, issue financial transactions, or mutate ERP/WMS state.
- **PII Masking:** Sanitizes customer node identifiers, exposing only non-sensitive operational attributes (order IDs, customer segments, shipping modes).
- **Sub-Millisecond Response:** In-memory caching ensures instant response times for dashboard visualizations.

---

## 2. API Endpoints

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/api/health` | Service health status, authoritative run ID, and active event ID. |
| `GET` | `/api/run` | Executive summary, gate verification results, and execution duration. |
| `GET` | `/api/lineage` | Full cryptographic execution trace across Stages 1 through 4. |
| `GET` | `/api/disruption` | Phase 7 disruption event payload with HDFS source metadata. |
| `GET` | `/api/shockwave` | Phase 8 graph shockwave metrics, cohort counts, and financial exposure. |
| `GET` | `/api/risk` | Phase 9 multi-dimensional risk scores, severity tiers, and priority orders. |
| `GET` | `/api/recovery/plans` | Side-by-side trade-off matrix of all 6 candidate recovery strategies. |
| `GET` | `/api/recovery/recommended` | Plan 5 (Knapsack Hybrid) explainability payload and allocations. |
| `GET` | `/api/recovery/stress-tests`| Complete 30-scenario counterfactual stress evaluation matrix. |
| `GET` | `/docs` | Interactive Swagger UI documentation. |
| `GET` | `/redoc` | Interactive ReDoc documentation. |

---

## 3. Manual Launch Instructions

To launch the FastAPI backend locally on port 8000:

```powershell
# From the project root (E:\BDA\ChainSentinel):
python web/backend/main.py
```
Or with Uvicorn CLI:
```powershell
cd E:\BDA\ChainSentinel\web\backend
uvicorn main:app --host 127.0.0.1 --port 8000
```
Swagger UI will be available at: `http://127.0.0.1:8000/docs`

---

## 4. Automated Testing

To run the backend test suite:

```powershell
python web/backend/tests/test_api.py
```
*Current Status:* 12/12 tests passing.

