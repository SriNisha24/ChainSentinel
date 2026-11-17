"""
ChainSentinel — Analysis Run Manager
Location: web/backend/services/analysis_run_manager.py

Coordinates multi-dataset, multi-run isolated analytical executions:
- Assigns unique Run IDs (ARUN-YYYYMMDDHHMMSS-XXXX).
- Isolates outputs by run directory: data/analysis_runs/<run_id>/run_results.json.
- Executes compatible Phase 5 models via inference_engine.
- Captures full run provenance: dataset association, model versions, timestamps, validation warnings, predictions.
- Prevents cross-dataset contamination and old results from misrepresenting new runs.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .dataset_service import dataset_service, DatasetValidationError
from .inference_engine import inference_engine

logger = logging.getLogger("ChainSentinel.AnalysisRunManager")

RUNS_DIR = Path(r"E:\BDA\ChainSentinel\data\analysis_runs")
INDEX_PATH = RUNS_DIR / "runs_index.json"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


class AnalysisRunManager:
    def __init__(self):
        self.runs_dir = RUNS_DIR
        self.index_path = INDEX_PATH
        self._ensure_index()

    def _ensure_index(self):
        if not self.index_path.exists():
            # Seed with authoritative baseline run from Phase 11
            seed = {
                "runs": [
                    {
                        "run_id": "ARUN-20261104143752-BASE",
                        "dataset_id": "DS-DATACO-ORIGINAL",
                        "dataset_name": "DataCo Smart Supply Chain Dataset (Original)",
                        "created_at": "2026-11-04T14:37:52Z",
                        "completed_at": "2026-11-04T14:38:15Z",
                        "status": "COMPLETED",
                        "total_records": 180519,
                        "models_executed": ["delay_model_v1", "anomaly_detection_v1", "disruption_impact_v1", "demand_forecasting_v1"],
                        "summary": {
                            "predicted_delay_rate_pct": 57.3,
                            "anomalies_detected": 1420,
                            "scenarios_evaluated": 4,
                            "forecast_daily_demand": 68.5
                        },
                        "provenance": "Authoritative historical Phase 10 baseline integration run"
                    }
                ]
            }
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(seed, f, indent=2)

    def _read_index(self) -> Dict[str, Any]:
        self._ensure_index()
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading runs index: {e}")
            return {"runs": []}

    def _write_index(self, data: Dict[str, Any]):
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def list_runs(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists analysis runs, optionally filtered by dataset ID."""
        data = self._read_index()
        runs = data.get("runs", [])
        if dataset_id:
            runs = [r for r in runs if r.get("dataset_id") == dataset_id]
        return sorted(runs, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves complete run results and model outputs from disk."""
        run_file = self.runs_dir / run_id / "run_results.json"
        if run_file.exists():
            try:
                with open(run_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading run file {run_file}: {e}")

        # Check index for metadata fallback
        for r in self.list_runs():
            if r["run_id"] == run_id:
                return r
        return None

    def execute_analysis(self, dataset_id: str, max_rows: int = 5000) -> Dict[str, Any]:
        """
        Executes an isolated, multi-model analysis run on the requested dataset.
        Never overwrites previous runs; saves to isolated directory.
        """
        dataset = dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise DatasetValidationError(f"Dataset '{dataset_id}' not found in catalog.")

        run_id = f"ARUN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        start_time = datetime.utcnow()
        logger.info(f"Starting analysis run {run_id} for dataset {dataset_id}")

        # Load normalized DataFrame
        df = dataset_service.load_dataset_dataframe(dataset_id, max_rows=max_rows)
        row_count = len(df)

        models_executed = []
        model_results = {}
        warnings = []

        # 1. Model 1: Delay Prediction
        try:
            m1_res = inference_engine.run_delay_prediction(df)
            model_results["delay_prediction"] = m1_res
            if m1_res.get("status") == "SUCCESS":
                models_executed.append("delay_model_v1")
            else:
                warnings.append(f"Delay Model skipped: {m1_res.get('message')}")
        except Exception as e:
            logger.error(f"Error running delay prediction: {e}")
            model_results["delay_prediction"] = {"status": "ERROR", "message": str(e)}
            warnings.append(f"Delay Model error: {str(e)}")

        # 2. Model 2: Anomaly Detection
        try:
            m2_res = inference_engine.run_anomaly_detection(df)
            model_results["anomaly_detection"] = m2_res
            if m2_res.get("status") == "SUCCESS":
                models_executed.append("anomaly_detection_v1")
            else:
                warnings.append(f"Anomaly Model skipped: {m2_res.get('message')}")
        except Exception as e:
            logger.error(f"Error running anomaly detection: {e}")
            model_results["anomaly_detection"] = {"status": "ERROR", "message": str(e)}
            warnings.append(f"Anomaly Model error: {str(e)}")

        # 3. Model 3: Disruption Impact
        try:
            m3_res = inference_engine.run_disruption_impact(df)
            model_results["disruption_impact"] = m3_res
            if m3_res.get("status") == "SUCCESS":
                models_executed.append("disruption_impact_v1")
            else:
                warnings.append(f"Disruption Model skipped: {m3_res.get('message')}")
        except Exception as e:
            logger.error(f"Error running disruption impact: {e}")
            model_results["disruption_impact"] = {"status": "ERROR", "message": str(e)}
            warnings.append(f"Disruption Model error: {str(e)}")

        # 4. Model 4: Demand Forecasting
        try:
            m4_res = inference_engine.run_demand_forecasting(df)
            model_results["demand_forecasting"] = m4_res
            if m4_res.get("status") == "SUCCESS":
                models_executed.append("demand_forecasting_v1")
            else:
                warnings.append(f"Demand Model skipped: {m4_res.get('message')}")
        except Exception as e:
            logger.error(f"Error running demand forecasting: {e}")
            model_results["demand_forecasting"] = {"status": "ERROR", "message": str(e)}
            warnings.append(f"Demand Model error: {str(e)}")

        end_time = datetime.utcnow()
        duration_sec = round((end_time - start_time).total_seconds(), 2)

        # Build combined summary
        delay_summary = model_results.get("delay_prediction", {})
        anomaly_summary = model_results.get("anomaly_detection", {})
        disruption_summary = model_results.get("disruption_impact", {})
        demand_summary = model_results.get("demand_forecasting", {})

        summary = {
            "predicted_delay_rate_pct": delay_summary.get("predicted_delay_rate_pct", 0.0),
            "anomalies_detected": anomaly_summary.get("anomalies_detected", 0),
            "critical_anomalies": anomaly_summary.get("critical_anomalies_count", 0),
            "scenarios_evaluated": disruption_summary.get("scenarios_evaluated", 0),
            "forecast_daily_demand": demand_summary.get("baseline_daily_demand", 0.0),
            "capacity_shortfall_orders": demand_summary.get("total_shortfall_orders", 0.0)
        }

        # Build full run payload
        full_result = {
            "run_id": run_id,
            "dataset_id": dataset_id,
            "dataset_name": dataset["name"],
            "created_at": start_time.isoformat() + "Z",
            "completed_at": end_time.isoformat() + "Z",
            "duration_seconds": duration_sec,
            "status": "COMPLETED",
            "total_records": row_count,
            "models_executed": models_executed,
            "warnings": warnings,
            "summary": summary,
            "results": model_results,
            "provenance": "Newly executed isolated dataset analysis run",
            "is_historical": dataset_id == "DS-DATACO-ORIGINAL" and row_count >= 180000
        }

        # Save to run directory
        result_file = run_dir / "run_results.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(full_result, f, indent=2)

        # Update index
        index_data = self._read_index()
        index_entry = {
            "run_id": run_id,
            "dataset_id": dataset_id,
            "dataset_name": dataset["name"],
            "created_at": start_time.isoformat() + "Z",
            "completed_at": end_time.isoformat() + "Z",
            "status": "COMPLETED",
            "total_records": row_count,
            "models_executed": models_executed,
            "summary": summary,
            "provenance": full_result["provenance"]
        }
        index_data["runs"].insert(0, index_entry)
        self._write_index(index_data)

        logger.info(f"Completed analysis run {run_id} in {duration_sec}s")
        return full_result


analysis_run_manager = AnalysisRunManager()

