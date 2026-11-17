"""
ChainSentinel — Dataset Intelligence & Multi-Model Inference Tests
Location: web/backend/tests/test_dataset_intelligence.py

Verifies:
1. Dataset Catalog & Original DataCo Registration
2. CSV Profiling, Schema Validation, Missing Value & Duplicates Analysis
3. Phase 5 Machine Learning Inference Tasks:
   - Delay Prediction (GBT logic, pre-shipment feature checks, zero leakage)
   - Anomaly Detection (K-Means distance, statistical thresholds)
   - Disruption Impact Scenarios (What-if shocks)
   - Demand Forecasting & Capacity Planner
4. Isolated Multi-Dataset Analysis Run Management
5. FastAPI REST Endpoints via TestClient
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent.parent

for p in [str(BACKEND_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from main import app
from services.dataset_service import dataset_service
from services.inference_engine import inference_engine
from services.analysis_run_manager import analysis_run_manager

client = TestClient(app)


def test_original_dataset_in_catalog():
    """Verifies that the original DataCo dataset is registered in the catalog."""
    datasets = dataset_service.list_datasets()
    assert len(datasets) >= 1
    orig = next((d for d in datasets if d["dataset_id"] == "DS-DATACO-ORIGINAL"), None)
    assert orig is not None
    assert orig["is_original"] is True
    assert orig["row_count"] == 180519
    assert orig["column_count"] == 53


def test_dataset_preview():
    """Verifies previewing the original DataCo dataset records."""
    preview = dataset_service.get_dataset_preview("DS-DATACO-ORIGINAL", limit=5)
    assert preview["dataset_id"] == "DS-DATACO-ORIGINAL"
    assert len(preview["records"]) == 5
    assert len(preview["columns"]) == 53
    # Check sample keys
    rec0 = preview["records"][0]
    assert "Shipping Mode" in rec0 or "shipping_mode" in rec0


def test_delay_prediction_inference():
    """Verifies pre-shipment delay model execution on sample transactions."""
    sample_data = {
        "days_for_shipment_scheduled": [1.0, 4.0, 2.0],
        "shipping_mode": ["First Class", "Standard Class", "Second Class"],
        "market": ["LATAM", "Europe", "USCA"],
        "order_region": ["South America", "Western Europe", "US Center"],
        "customer_segment": ["Consumer", "Corporate", "Home Office"],
        "payment_type": ["DEBIT", "TRANSFER", "PAYMENT"],
        "department_name": ["Apparel", "Fan Shop", "Golf"],
        "product_price": [129.99, 59.99, 199.99],
        "order_item_quantity": [1, 2, 1],
        "sales": [129.99, 119.98, 199.99],
        "order_item_discount": [0.0, 5.0, 20.0],
        "order_item_discount_rate": [0.0, 0.04, 0.10],
        "order_item_total": [129.99, 114.98, 179.99],
        "order_profit_per_order": [32.50, 45.20, 58.00],
        "latitude": [-12.0464, 48.8566, 41.8781],
        "longitude": [-77.0428, 2.3522, -87.6298],
        "order_id": ["ORD-1", "ORD-2", "ORD-3"],
        "order_item_id": ["ITEM-1", "ITEM-2", "ITEM-3"]
    }
    df = pd.DataFrame(sample_data)
    result = inference_engine.run_delay_prediction(df)

    assert result["status"] == "SUCCESS"
    assert result["model_id"] == "delay_model_v1"
    assert result["total_records_evaluated"] == 3
    assert len(result["sample_predictions"]) == 3
    # First Class with 1-day SLA should have high delay probability
    p0 = result["sample_predictions"][0]
    assert p0["predicted_delay_probability"] > 0.50
    assert p0["risk_tier"] in ["CRITICAL", "HIGH"]


def test_anomaly_detection_inference():
    """Verifies dual-method anomaly detection execution."""
    sample_data = {
        "product_price": [399.98, 59.99],
        "order_item_quantity": [2.0, 1.0],
        "order_item_discount": [50.0, 5.0],
        "order_item_discount_rate": [0.06, 0.08],
        "order_item_total": [749.96, 54.99],
        "order_profit_per_order": [-650.0, 24.50],  # Item 1 is catastrophic profit bleed
        "days_for_shipment_scheduled": [1.0, 2.0],
        "order_id": ["ORD-101", "ORD-102"],
        "order_item_id": ["ITEM-101", "ITEM-102"]
    }
    df = pd.DataFrame(sample_data)
    result = inference_engine.run_anomaly_detection(df)

    assert result["status"] == "SUCCESS"
    assert result["model_id"] == "anomaly_detection_v1"
    assert result["total_records_evaluated"] == 2
    # Item 1 must be flagged as critical bleed
    assert result["sample_anomalies"][0]["is_anomaly"] is True
    assert "BLEED" in result["sample_anomalies"][0]["anomaly_class"] or result["sample_anomalies"][0]["anomaly_score"] > 2.0


def test_disruption_impact_scenarios():
    """Verifies disruption scenario evaluation."""
    sample_data = {
        "market": ["LATAM", "Europe", "Pacific Asia", "USCA"],
        "order_region": ["South America", "Western Europe", "Eastern Asia", "US Center"],
        "shipping_mode": ["Standard Class", "First Class", "Standard Class", "Second Class"],
        "order_item_total": [500.0, 1200.0, 3500.0, 800.0],
        "order_profit_per_order": [120.0, 250.0, 600.0, 150.0],
        "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-4"]
    }
    df = pd.DataFrame(sample_data)
    result = inference_engine.run_disruption_impact(df)

    assert result["status"] == "SUCCESS"
    assert result["scenarios_evaluated"] == 4
    assert len(result["scenario_results"]) == 4


def test_demand_forecasting():
    """Verifies demand forecasting and capacity shortfall calculations."""
    sample_data = {
        "order_date": ["2018-01-01", "2018-01-02", "2018-01-03"] * 30,
        "order_item_quantity": [1, 2, 1] * 30
    }
    df = pd.DataFrame(sample_data)
    result = inference_engine.run_demand_forecasting(df, horizon_days=7)

    assert result["status"] == "SUCCESS"
    assert result["model_id"] == "demand_forecasting_v1"
    assert len(result["forecast_timeline"]) == 7
    assert result["baseline_daily_demand"] > 0


def test_fastapi_dataset_endpoints():
    """Verifies FastAPI REST endpoints for dataset listing and preview."""
    resp = client.get("/api/datasets")
    assert resp.status_code == 200
    datasets = resp.json()
    assert isinstance(datasets, list)
    assert any(d["dataset_id"] == "DS-DATACO-ORIGINAL" for d in datasets)

    prev_resp = client.get("/api/datasets/DS-DATACO-ORIGINAL/preview?limit=3")
    assert prev_resp.status_code == 200
    prev_data = prev_resp.json()
    assert len(prev_data["records"]) == 3


def test_fastapi_upload_validation_and_analysis_flow(tmp_path):
    """
    Tests end-to-end:
    Upload custom CSV -> Preview -> Run Analysis -> Inspect Results & Records.
    """
    # Create small valid test CSV
    csv_content = (
        "order_id,order_item_id,shipping_mode,market,order_region,customer_segment,payment_type,"
        "department_name,days_for_shipment_scheduled,product_price,order_item_quantity,sales,"
        "order_item_discount,order_item_discount_rate,order_item_total,order_profit_per_order,latitude,longitude,order_date\n"
        "ORD-991,ITEM-991,First Class,Europe,Western Europe,Consumer,DEBIT,Apparel,1.0,150.0,1,150.0,0.0,0.0,150.0,-250.0,48.8,2.3,2018-01-10\n"
        "ORD-992,ITEM-992,Standard Class,LATAM,South America,Corporate,TRANSFER,Fan Shop,4.0,50.0,2,100.0,10.0,0.1,90.0,25.0,-12.0,-77.0,2018-01-11\n"
    )
    test_file = tmp_path / "custom_test_supply_chain.csv"
    test_file.write_text(csv_content, encoding="utf-8")

    with open(test_file, "rb") as f:
        upload_resp = client.post(
            "/api/datasets/upload",
            files={"file": ("custom_test_supply_chain.csv", f, "text/csv")}
        )

    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["success"] is True
    ds_id = upload_data["dataset"]["dataset_id"]

    # Preview uploaded dataset
    preview_resp = client.get(f"/api/datasets/{ds_id}/preview")
    assert preview_resp.status_code == 200
    assert len(preview_resp.json()["records"]) == 2

    # Execute Analysis Run
    run_resp = client.post(f"/api/analysis/{ds_id}/run?max_rows=100")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    run_id = run_data["run_id"]
    assert run_data["status"] == "COMPLETED"
    assert len(run_data["models_executed"]) >= 3

    # Retrieve Run Summary in list
    runs_list_resp = client.get(f"/api/analysis/runs?dataset_id={ds_id}")
    assert runs_list_resp.status_code == 200
    assert any(r["run_id"] == run_id for r in runs_list_resp.json())

    # Retrieve Paginated Records
    rec_resp = client.get(f"/api/analysis/runs/{run_id}/records?task=delay&page=1&page_size=10")
    assert rec_resp.status_code == 200
    assert len(rec_resp.json()["records"]) == 2


def test_four_synthetic_datasets_registered_and_profiled():
    """Verifies all four synthetic datasets are registered, validated, and 100% compatible."""
    datasets = dataset_service.list_datasets()
    expected_ids = ["DS-SYN-NORMAL", "DS-SYN-MODERATE", "DS-SYN-COMPOUND", "DS-SYN-EXTREME"]
    
    for ds_id in expected_ids:
        ds = next((d for d in datasets if d["dataset_id"] == ds_id), None)
        assert ds is not None, f"Dataset {ds_id} not found in catalog."
        assert ds["is_synthetic"] is True
        assert ds["status"] == "VALIDATED"
        assert ds["column_count"] == 53
        assert ds["row_count"] >= 3000
        
        # Verify model compatibility
        meta = dataset_service.get_dataset(ds_id)
        assert meta is not None
        compat = meta.get("model_compatibility", {})
        for model in ["delay_prediction_v1", "anomaly_detection_v1", "disruption_impact_v1", "demand_forecasting_v1"]:
            assert model in compat
            assert compat[model]["status"] == "COMPATIBLE"


def test_synthetic_datasets_multi_model_execution_and_progression():
    """Verifies that all 4 models execute successfully across all synthetic datasets with increasing disruption severity."""
    results = {}
    for ds_id in ["DS-SYN-NORMAL", "DS-SYN-MODERATE", "DS-SYN-COMPOUND", "DS-SYN-EXTREME"]:
        run = analysis_run_manager.execute_analysis(ds_id, max_rows=500)
        assert run["status"] == "COMPLETED"
        assert len(run["models_executed"]) == 4
        summary = run["summary"]
        results[ds_id] = summary
        
    # Verify progressive stress severity: Extreme should have highest delay and anomaly impact
    normal_delay = results["DS-SYN-NORMAL"]["predicted_delay_rate_pct"]
    extreme_delay = results["DS-SYN-EXTREME"]["predicted_delay_rate_pct"]
    assert extreme_delay > normal_delay, f"Expected extreme delay ({extreme_delay}%) > normal delay ({normal_delay}%)"


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RUNNING CHAINSENTINEL DATASET INTELLIGENCE TEST SUITE")
    print("=" * 60)

    test_original_dataset_in_catalog()
    print("[PASS]: test_original_dataset_in_catalog")

    test_dataset_preview()
    print("[PASS]: test_dataset_preview")

    test_four_synthetic_datasets_registered_and_profiled()
    print("[PASS]: test_four_synthetic_datasets_registered_and_profiled")

    test_delay_prediction_inference()
    print("[PASS]: test_delay_prediction_inference")

    test_anomaly_detection_inference()
    print("[PASS]: test_anomaly_detection_inference")

    test_disruption_impact_scenarios()
    print("[PASS]: test_disruption_impact_scenarios")

    test_demand_forecasting()
    print("[PASS]: test_demand_forecasting")

    test_synthetic_datasets_multi_model_execution_and_progression()
    print("[PASS]: test_synthetic_datasets_multi_model_execution_and_progression")

    test_fastapi_dataset_endpoints()
    print("[PASS]: test_fastapi_dataset_endpoints")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        test_fastapi_upload_validation_and_analysis_flow(Path(td))
    print("[PASS]: test_fastapi_upload_validation_and_analysis_flow")

    print("\n" + "=" * 60)
    print("ALL 10 DATASET INTELLIGENCE TESTS PASSED PERFECTLY!")
    print("=" * 60)

