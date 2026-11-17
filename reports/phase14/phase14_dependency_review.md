# ChainSentinel — Phase 14 Task 14F: Dependency and Configuration Review

**Document Reference:** `reports/phase14/phase14_dependency_review.md`  
**Execution Timestamp:** 2026-11-04T23:38:00+05:30  
**Scope:** Python Global Environment, Node/npm Packages, and Application Configuration  

---

## 1. Executive Summary

A comprehensive dependency and configuration review was performed across backend and frontend environments. No automatic dependency upgrades or unapproved installations were performed, adhering strictly to Mandatory Project Protection Rule #7.

---

## 2. Python Environment & Dependency Audit

The backend runs on Python 3.12 (Windows host global environment). Key dependencies include:

| Package | Version | Purpose | Security & Compatibility Assessment |
| :--- | :--- | :--- | :--- |
| `fastapi` | `0.110.0` | Core REST API Framework | Stable. Deprecation warning on Starlette 1.x handled via compatibility bridge in `main.py`. |
| `starlette` | `1.6.0` | ASGI Framework Underlying FastAPI | Active. Starlette 1.x parameter signatures accommodated. |
| `pydantic` | `2.6.3` | Schema & Payload Validation | Active. Protected namespace warning on `model_id` documented; strict field length limits enforced. |
| `uvicorn` | `0.52.4` | ASGI Server | Production-ready HTTP/1.1 ASGI server. |
| `pandas` | `2.2.3` | Analytical Data Loading & PII Masking | Stable. Zero known CVEs affecting current usage. |
| `scikit-learn` | `1.6.1` | Anomaly Detection Baseline Scoring | Stable. Used in Phase 5 & Phase 13 model evaluations. |
| `networkx` | `3.6.1` | Graph Shockwave Topology | Stable graph algorithm library. |
| `jsonschema` | `4.26.0` | Draft-07 Schema Validation | Enforces Draft-07 schemas for alerts, feedback, and approvals. |
| `httpx` | `0.28.1` | ASGI Test Client Integration | Testclient dependency. |

### Configuration Safeguards:
- Python standard library `hashlib` (PBKDF2-HMAC-SHA256) and `secrets` used for authentication and token generation, avoiding external crypto dependencies.
- Standard library `collections.defaultdict` and `time` used for in-memory rate limiting.

---

## 3. Frontend npm Environment Audit

The frontend operates under `web/frontend/` built with Vite 8 and React 19:

| Package | Version | Role | Assessment |
| :--- | :--- | :--- | :--- |
| `react` | `^19.3.1` | UI Library | Production build verified (`tsc -b && vite build` clean). |
| `react-dom` | `^19.3.1` | DOM Renderer | Modern React 19 features active. |
| `vite` | `^8.3.5` | Build Tool & Bundler | Modern ESM build pipeline; production bundle size: 747 kB JS / 47 kB CSS. |
| `recharts` | `^3.10.1` | Operational Visualizations | Interactive SVG charting for financial and risk cohorts. |
| `lucide-react` | `^1.68.0` | UI Icons | SVG iconography. |
| `tailwindcss` | `^4.3.4` | Utility Styling | Modern Tailwind CSS 4 engine. |

---

## 4. Environment Configuration & Secret Management

1. **Zero Hardcoded Secrets in Git:**
   - Password hashes in `auth_service.py` are one-way salted PBKDF2 hashes (100,000 rounds).
   - Session tokens are generated dynamically at runtime via CSPRNG (`secrets.token_hex(32)`).
2. **Template Configuration:**
   - `.env.example` created in `web/backend/` providing safe placeholder configuration variables.

---

## 5. Recommendations for Future Upgrades (Post-Project)

1. **FastAPI Upgrade:** In future maintenance cycles (outside project scope), upgrade `fastapi` to `>=0.115` to natively align with Starlette 1.x router signatures without the custom compatibility bridge.
2. **Frontend Chunk Splitting:** Introduce dynamic `import()` in Vite configuration to split dashboard modules into bundles &lt; 500 kB.

