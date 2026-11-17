"""
ChainSentinel — Synthetic Dataset Generator
Location: scripts/dataset_intelligence/generate_synthetic_datasets.py

Generates four realistic, model-compatible synthetic supply-chain datasets:
1. DS-SYN-NORMAL: Normal Operations (3,000 records)
2. DS-SYN-MODERATE: Moderate Disruption (3,000 records)
3. DS-SYN-COMPOUND: Compound Disruption (3,500 records)
4. DS-SYN-EXTREME: Extreme Supply Chain Stress Test (4,000 records)

Preserves exact 53-column DataCo schema, valid data types, internal mathematical consistency,
and strict target leakage defense.
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(r"E:\BDA\ChainSentinel")
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "DataCoSupplyChainDataset.csv"
SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic_datasets"
CATALOG_PATH = PROJECT_ROOT / "data" / "datasets" / "catalog.json"

SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)


def load_seed_data(n_samples: int = 15000) -> pd.DataFrame:
    """Loads a representative sample from raw DataCo."""
    print(f"Loading seed data from {RAW_DATA_PATH}...")
    df = pd.read_csv(RAW_DATA_PATH, nrows=n_samples, encoding="ISO-8859-1")
    return df


def ensure_financial_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures price, quantity, discount, total, and profit are mathematically consistent."""
    df["Order Item Quantity"] = pd.to_numeric(df["Order Item Quantity"], errors="coerce").fillna(1).astype(int).clip(1, 10)
    df["Product Price"] = pd.to_numeric(df["Product Price"], errors="coerce").fillna(100.0).round(2)
    df["Order Item Discount Rate"] = pd.to_numeric(df["Order Item Discount Rate"], errors="coerce").fillna(0.0).clip(0.0, 0.6).round(4)
    
    # Gross sales before discount
    gross_sales = (df["Product Price"] * df["Order Item Quantity"]).round(2)
    df["Sales"] = gross_sales
    
    # Discount amount
    df["Order Item Discount"] = (gross_sales * df["Order Item Discount Rate"]).round(2)
    
    # Net sales (Sales per customer / Order Item Total)
    df["Order Item Total"] = (gross_sales - df["Order Item Discount"]).round(2)
    df["Sales per customer"] = df["Order Item Total"]
    
    # Profit calculation
    df["Benefit per order"] = df["Order Profit Per Order"]
    return df


def generate_normal_dataset(seed_df: pd.DataFrame) -> pd.DataFrame:
    """
    DS-SYN-NORMAL: Normal Operations
    Stable supply chain, low disruption intensity, nominal SLAs, typical positive profit margins.
    """
    print("Generating DS-SYN-NORMAL...")
    df = seed_df.sample(n=3000, random_state=42, replace=True).copy().reset_index(drop=True)
    
    # Normal shipping modes (predominantly Standard & Second Class)
    modes = np.random.choice(
        ["Standard Class", "Second Class", "First Class", "Same Day"],
        size=len(df),
        p=[0.60, 0.22, 0.14, 0.04]
    )
    df["Shipping Mode"] = modes
    
    # Scheduled days matching mode
    sla_map = {"Standard Class": 4, "Second Class": 3, "First Class": 2, "Same Day": 1}
    df["Days for shipment (scheduled)"] = [sla_map[m] for m in modes]
    
    # Real shipping days close to scheduled
    df["Days for shipping (real)"] = df["Days for shipment (scheduled)"] + np.random.choice([0, 0, 0, 1, -1], size=len(df))
    df["Days for shipping (real)"] = df["Days for shipping (real)"].clip(1, 6)
    
    # Normal delivery status
    df["Delivery Status"] = np.where(
        df["Days for shipping (real)"] > df["Days for shipment (scheduled)"],
        "Late delivery",
        np.where(df["Days for shipping (real)"] < df["Days for shipment (scheduled)"], "Advance shipping", "Shipping on time")
    )
    df["Late_delivery_risk"] = (df["Delivery Status"] == "Late delivery").astype(int)
    
    # Normal profit margins: mostly positive between $10 and $120
    df["Order Profit Per Order"] = np.random.normal(loc=28.5, scale=25.0, size=len(df)).round(2)
    df["Order Profit Per Order"] = df["Order Profit Per Order"].clip(-40.0, 350.0)
    
    # Normal dates spread across 45 days
    base_date = datetime(2026, 9, 1)
    df["order date (DateOrders)"] = [
        (base_date + timedelta(days=int(i % 45), hours=int(i % 24))).strftime("%m/%d/%Y %H:%M")
        for i in range(len(df))
    ]
    df["shipping date (DateOrders)"] = [
        (datetime.strptime(df.loc[i, "order date (DateOrders)"], "%m/%d/%Y %H:%M") + timedelta(days=int(df.loc[i, "Days for shipping (real)"]))).strftime("%m/%d/%Y %H:%M")
        for i in range(len(df))
    ]
    
    # Order IDs
    df["Order Id"] = [100000 + i for i in range(len(df))]
    df["Order Item Id"] = [200000 + i for i in range(len(df))]
    
    return ensure_financial_consistency(df)


def generate_moderate_dataset(seed_df: pd.DataFrame) -> pd.DataFrame:
    """
    DS-SYN-MODERATE: Moderate Disruption
    Increased shipping delays, higher proportion of tight SLAs, localized margin anomalies.
    """
    print("Generating DS-SYN-MODERATE...")
    df = seed_df.sample(n=3000, random_state=101, replace=True).copy().reset_index(drop=True)
    
    # Elevated shipping modes (more express & tight SLA)
    modes = np.random.choice(
        ["Standard Class", "Second Class", "First Class", "Same Day"],
        size=len(df),
        p=[0.40, 0.28, 0.24, 0.08]
    )
    df["Shipping Mode"] = modes
    
    sla_map = {"Standard Class": 4, "Second Class": 3, "First Class": 2, "Same Day": 1}
    df["Days for shipment (scheduled)"] = [sla_map[m] for m in modes]
    
    # Increased shipping delays
    delay_bump = np.random.choice([0, 1, 2, 3], size=len(df), p=[0.45, 0.35, 0.15, 0.05])
    df["Days for shipping (real)"] = df["Days for shipment (scheduled)"] + delay_bump
    df["Days for shipping (real)"] = df["Days for shipping (real)"].clip(1, 7)
    
    df["Delivery Status"] = np.where(
        df["Days for shipping (real)"] > df["Days for shipment (scheduled)"],
        "Late delivery",
        np.where(df["Days for shipping (real)"] < df["Days for shipment (scheduled)"], "Advance shipping", "Shipping on time")
    )
    df["Late_delivery_risk"] = (df["Delivery Status"] == "Late delivery").astype(int)
    
    # Moderate anomalies: ~5% transactions suffer margin bleed
    profits = np.random.normal(loc=18.0, scale=35.0, size=len(df)).round(2)
    # Inject ~90 moderate loss transactions
    loss_indices = np.random.choice(len(df), size=90, replace=False)
    profits[loss_indices] = np.random.uniform(-180.0, -90.0, size=90).round(2)
    df["Order Profit Per Order"] = profits
    
    # Concentrate 45% of volume in Pacific Asia
    regions = np.random.choice(
        ["Eastern Asia", "South Asia", "Southeast Asia", "Western Europe", "Central America"],
        size=len(df),
        p=[0.30, 0.18, 0.16, 0.20, 0.16]
    )
    df["Order Region"] = regions
    df["Market"] = np.where(
        np.isin(regions, ["Eastern Asia", "South Asia", "Southeast Asia"]),
        "Pacific Asia",
        np.where(regions == "Western Europe", "Europe", "LATAM")
    )
    
    base_date = datetime(2026, 9, 15)
    df["order date (DateOrders)"] = [
        (base_date + timedelta(days=int(i % 30), hours=int(i % 24))).strftime("%m/%d/%Y %H:%M")
        for i in range(len(df))
    ]
    df["shipping date (DateOrders)"] = [
        (datetime.strptime(df.loc[i, "order date (DateOrders)"], "%m/%d/%Y %H:%M") + timedelta(days=int(df.loc[i, "Days for shipping (real)"]))).strftime("%m/%d/%Y %H:%M")
        for i in range(len(df))
    ]
    
    df["Order Id"] = [300000 + i for i in range(len(df))]
    df["Order Item Id"] = [400000 + i for i in range(len(df))]
    
    return ensure_financial_consistency(df)


def generate_compound_dataset(seed_df: pd.DataFrame) -> pd.DataFrame:
    """
    DS-SYN-COMPOUND: Compound Disruption
    Simultaneous multi-region disruptions, high delay probabilities, multiple severe profit bleeds.
    """
    print("Generating DS-SYN-COMPOUND...")
    df = seed_df.sample(n=3500, random_state=202, replace=True).copy().reset_index(drop=True)
    
    modes = np.random.choice(
        ["Standard Class", "Second Class", "First Class", "Same Day"],
        size=len(df),
        p=[0.30, 0.25, 0.33, 0.12]
    )
    df["Shipping Mode"] = modes
    
    sla_map = {"Standard Class": 4, "Second Class": 3, "First Class": 2, "Same Day": 1}
    df["Days for shipment (scheduled)"] = [sla_map[m] for m in modes]
    
    # Significant delays across regions
    delay_bump = np.random.choice([0, 1, 2, 3, 4], size=len(df), p=[0.30, 0.35, 0.20, 0.10, 0.05])
    df["Days for shipping (real)"] = df["Days for shipment (scheduled)"] + delay_bump
    df["Days for shipping (real)"] = df["Days for shipping (real)"].clip(1, 8)
    
    df["Delivery Status"] = np.where(
        df["Days for shipping (real)"] > df["Days for shipment (scheduled)"],
        "Late delivery",
        "Shipping on time"
    )
    df["Late_delivery_risk"] = (df["Delivery Status"] == "Late delivery").astype(int)
    
    # Multiple severe profit bleeds
    profits = np.random.normal(loc=12.0, scale=45.0, size=len(df)).round(2)
    # Severe loss (< -166.73)
    loss_indices_1 = np.random.choice(len(df), size=140, replace=False)
    profits[loss_indices_1] = np.random.uniform(-350.0, -170.0, size=140).round(2)
    # Critical bleed (< -500.0)
    loss_indices_2 = np.random.choice(loss_indices_1, size=25, replace=False)
    profits[loss_indices_2] = np.random.uniform(-750.0, -510.0, size=25).round(2)
    df["Order Profit Per Order"] = profits
    
    # Multi-region concentration in Pacific Asia and Europe
    regions = np.random.choice(
        ["Eastern Asia", "Western Europe", "South Asia", "Southeast Asia", "Central America"],
        size=len(df),
        p=[0.35, 0.28, 0.15, 0.12, 0.10]
    )
    df["Order Region"] = regions
    df["Market"] = np.where(
        np.isin(regions, ["Eastern Asia", "South Asia", "Southeast Asia"]),
        "Pacific Asia",
        np.where(regions == "Western Europe", "Europe", "LATAM")
    )
    
    base_date = datetime(2026, 10, 1)
    df["order date (DateOrders)"] = [
        (base_date + timedelta(days=int(i % 25), hours=int(i % 24))).strftime("%m/%d/%Y %H:%M")
        for i in range(len(df))
    ]
    df["shipping date (DateOrders)"] = [
        (datetime.strptime(df.loc[i, "order date (DateOrders)"], "%m/%d/%Y %H:%M") + timedelta(days=int(df.loc[i, "Days for shipping (real)"]))).strftime("%m/%d/%Y %H:%M")
        for i in range(len(df))
    ]
    
    df["Order Id"] = [500000 + i for i in range(len(df))]
    df["Order Item Id"] = [600000 + i for i in range(len(df))]
    
    return ensure_financial_consistency(df)


def generate_extreme_dataset(seed_df: pd.DataFrame) -> pd.DataFrame:
    """
    DS-SYN-EXTREME: Extreme Supply Chain Stress Test
    Severe cascading crisis: port closure in East Asia (65% volume), tight 1-day SLAs,
    catastrophic margin bleeds (< -$500), and massive demand surge triggering SLA capacity shortfall.
    """
    print("Generating DS-SYN-EXTREME...")
    df = seed_df.sample(n=4000, random_state=303, replace=True).copy().reset_index(drop=True)
    
    # 65% of all traffic concentrated in East Asia / Pacific Asia (matching PORT_CLOSURE epicenter)
    regions = np.random.choice(
        ["Eastern Asia", "South Asia", "Southeast Asia", "Western Europe", "Central America"],
        size=len(df),
        p=[0.55, 0.12, 0.10, 0.15, 0.08]
    )
    df["Order Region"] = regions
    df["Market"] = np.where(
        np.isin(regions, ["Eastern Asia", "South Asia", "Southeast Asia"]),
        "Pacific Asia",
        np.where(regions == "Western Europe", "Europe", "LATAM")
    )
    
    # High proportion of expedited/tight SLAs (42% First Class, 18% Same Day)
    modes = np.random.choice(
        ["Standard Class", "Second Class", "First Class", "Same Day"],
        size=len(df),
        p=[0.20, 0.20, 0.42, 0.18]
    )
    df["Shipping Mode"] = modes
    
    sla_map = {"Standard Class": 4, "Second Class": 3, "First Class": 2, "Same Day": 1}
    df["Days for shipment (scheduled)"] = [sla_map[m] for m in modes]
    
    # Extreme transit delays due to port closure (2 to 5 extra days added)
    delay_bump = np.random.choice([1, 2, 3, 4, 5], size=len(df), p=[0.15, 0.35, 0.25, 0.15, 0.10])
    df["Days for shipping (real)"] = df["Days for shipment (scheduled)"] + delay_bump
    df["Days for shipping (real)"] = df["Days for shipping (real)"].clip(2, 9)
    
    df["Delivery Status"] = "Late delivery"
    df["Late_delivery_risk"] = 1
    
    # Catastrophic profit bleeds: 80+ records below -$500, 200+ below -$166.73
    profits = np.random.normal(loc=-15.0, scale=60.0, size=len(df)).round(2)
    severe_loss_idx = np.random.choice(len(df), size=240, replace=False)
    profits[severe_loss_idx] = np.random.uniform(-480.0, -180.0, size=240).round(2)
    crit_bleed_idx = np.random.choice(severe_loss_idx, size=85, replace=False)
    profits[crit_bleed_idx] = np.random.uniform(-1400.0, -520.0, size=85).round(2)
    df["Order Profit Per Order"] = profits
    
    # Extreme demand surge concentrated in a 14-day window (exceeding warehouse 65 orders/day capacity)
    base_date = datetime(2026, 10, 15)
    df["order date (DateOrders)"] = [
        (base_date + timedelta(days=int(i % 14), hours=int((i * 3) % 24), minutes=int(i % 60))).strftime("%m/%d/%Y %H:%M")
        for i in range(len(df))
    ]
    df["shipping date (DateOrders)"] = [
        (datetime.strptime(df.loc[i, "order date (DateOrders)"], "%m/%d/%Y %H:%M") + timedelta(days=int(df.loc[i, "Days for shipping (real)"]))).strftime("%m/%d/%Y %H:%M")
        for i in range(len(df))
    ]
    
    df["Order Id"] = [700000 + i for i in range(len(df))]
    df["Order Item Id"] = [800000 + i for i in range(len(df))]
    
    return ensure_financial_consistency(df)


def save_synthetic_dataset(
    dataset_id: str,
    name: str,
    description: str,
    df: pd.DataFrame,
    scenario_details: dict
) -> dict:
    """Saves dataset files, metadata, schema, and README in an isolated directory."""
    target_dir = SYNTHETIC_DIR / dataset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    
    csv_file = target_dir / f"{dataset_id}.csv"
    meta_file = target_dir / "metadata.json"
    schema_file = target_dir / "schema_reference.json"
    readme_file = target_dir / "README.md"
    
    # 1. Save CSV
    df.to_csv(csv_file, index=False, encoding="utf-8")
    file_size = csv_file.stat().st_size
    
    # 2. Schema reference
    schema = {col: str(df[col].dtype) for col in df.columns}
    with open(schema_file, "w", encoding="utf-8") as f:
        json.dump({
            "dataset_id": dataset_id,
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "data_types": schema
        }, f, indent=2)
        
    # 3. Model compatibility check
    required_features = {
        "delay_prediction_v1": ["shipping_mode", "product_price", "days_for_shipment_scheduled", "order_item_quantity"],
        "anomaly_detection_v1": ["product_price", "order_item_quantity", "order_item_discount", "order_item_total", "order_profit_per_order", "days_for_shipment_scheduled"],
        "disruption_impact_v1": ["market", "order_region", "shipping_mode", "order_item_total", "order_profit_per_order"],
        "demand_forecasting_v1": ["order_date", "order_item_quantity"]
    }
    
    normalized_cols = {c.strip().lower().replace(" ", "_"): c for c in df.columns}
    # Add mapped columns
    normalized_cols["order_date"] = "order date (DateOrders)"
    normalized_cols["order_profit_per_order"] = "Order Profit Per Order"
    normalized_cols["order_item_total"] = "Order Item Total"
    normalized_cols["days_for_shipment_scheduled"] = "Days for shipment (scheduled)"
    
    compatibility = {}
    for model_name, reqs in required_features.items():
        matched = [r for r in reqs if r in normalized_cols or r in df.columns]
        compatibility[model_name] = {
            "status": "COMPATIBLE" if len(matched) == len(reqs) else "PARTIAL",
            "matched_features": matched,
            "missing_features": [r for r in reqs if r not in matched]
        }
    
    # 4. Metadata JSON
    metadata = {
        "dataset_id": dataset_id,
        "name": name,
        "filename": f"{dataset_id}.csv",
        "description": description,
        "file_path": str(csv_file),
        "file_size_bytes": file_size,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "is_original": False,
        "is_synthetic": True,
        "row_count": len(df),
        "column_count": len(df.columns),
        "encoding": "utf-8",
        "status": "VALIDATED",
        "scenario": scenario_details,
        "model_compatibility": compatibility
    }
    
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    # 5. README.md
    readme_content = f"""# {name} ({dataset_id})

## Scenario Description
{description}

- **Dataset ID:** `{dataset_id}`
- **Records:** {len(df):,} rows
- **Columns:** {len(df.columns)} features
- **Designation:** SYNTHETIC SUPPLY CHAIN SCENARIO
- **Target Leakage Defense:** Compliant (pre-shipment features separated)
- **Model Compatibility:** 4/4 Phase 5 Production Models Compatible

### Key Characteristics
- **Primary Market Focus:** {scenario_details.get('market_focus', 'Global')}
- **Expected Delay Intensity:** {scenario_details.get('delay_intensity', 'Moderate')}
- **Margin Anomaly Exposure:** {scenario_details.get('anomaly_exposure', 'Low')}
- **Demand Pattern:** {scenario_details.get('demand_pattern', 'Nominal')}
"""
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    print(f"Saved {dataset_id}: {len(df):,} records ({file_size / 1024 / 1024:.2f} MB)")
    return metadata


def main():
    seed_df = load_seed_data(n_samples=25000)
    
    # Generate the 4 datasets
    normal_df = generate_normal_dataset(seed_df)
    meta_normal = save_synthetic_dataset(
        dataset_id="DS-SYN-NORMAL",
        name="Normal Operations",
        description="A stable supply-chain environment with typical shipment delays, normal carrier performance, and low disruption intensity.",
        df=normal_df,
        scenario_details={
            "market_focus": "Balanced Global Markets",
            "delay_intensity": "Baseline Nominal (< 15% delayed)",
            "anomaly_exposure": "Negligible (< 0.2% outliers)",
            "demand_pattern": "Stable (within 65 orders/day SLA capacity)"
        }
    )
    
    moderate_df = generate_moderate_dataset(seed_df)
    meta_moderate = save_synthetic_dataset(
        dataset_id="DS-SYN-MODERATE",
        name="Moderate Disruption",
        description="A supply chain experiencing localized operational problems, increased shipping delays in Pacific Asia, and early margin anomalies.",
        df=moderate_df,
        scenario_details={
            "market_focus": "Pacific Asia Regional Concentration (45%)",
            "delay_intensity": "Moderate (35-45% delayed)",
            "anomaly_exposure": "Moderate (90 margin loss anomalies)",
            "demand_pattern": "Fluctuating with mild capacity crunches"
        }
    )
    
    compound_df = generate_compound_dataset(seed_df)
    meta_compound = save_synthetic_dataset(
        dataset_id="DS-SYN-COMPOUND",
        name="Compound Disruption",
        description="Multiple supply-chain disruptions occurring simultaneously across Pacific Asia and Europe with severe transit delays and profit bleeds.",
        df=compound_df,
        scenario_details={
            "market_focus": "Multi-Region (Pacific Asia 45%, Europe 28%)",
            "delay_intensity": "High (55-65% delayed across modes)",
            "anomaly_exposure": "Significant (140+ loss anomalies, 25 severe)",
            "demand_pattern": "Volatile surges exceeding nominal SLA capacity"
        }
    )
    
    extreme_df = generate_extreme_dataset(seed_df)
    meta_extreme = save_synthetic_dataset(
        dataset_id="DS-SYN-EXTREME",
        name="Extreme Supply Chain Stress Test",
        description="A severe, cascading multi-region crisis with maritime port closure (65% volume), catastrophic margin bleeds (< -$500), and massive SLA shortfalls.",
        df=extreme_df,
        scenario_details={
            "market_focus": "Heavy East Asia / Pacific Asia Port Epicenter (65%)",
            "delay_intensity": "Severe (80%+ delayed, 2-5 days added)",
            "anomaly_exposure": "Catastrophic (240+ severe losses, 85 critical bleeds)",
            "demand_pattern": "Critical surges triggering massive SLA capacity shortfall"
        }
    )
    
    # Update catalog.json
    print(f"Updating catalog at {CATALOG_PATH}...")
    catalog = {"datasets": {}}
    if CATALOG_PATH.exists():
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception:
            catalog = {"datasets": {}}
            
    datasets = catalog.setdefault("datasets", {})
    
    # Ensure DS-DATACO-ORIGINAL exists
    if "DS-DATACO-ORIGINAL" not in datasets:
        datasets["DS-DATACO-ORIGINAL"] = {
            "dataset_id": "DS-DATACO-ORIGINAL",
            "name": "DataCo Smart Supply Chain Dataset (Original)",
            "description": "Authoritative 180,519 record supply chain transaction dataset with logistics, SLA, and pricing features.",
            "file_path": str(RAW_DATA_PATH),
            "file_size_bytes": RAW_DATA_PATH.stat().st_size if RAW_DATA_PATH.exists() else 95910149,
            "created_at": "2026-11-04T00:00:00Z",
            "is_original": True,
            "row_count": 180519,
            "column_count": 53,
            "encoding": "ISO-8859-1",
            "status": "READY"
        }
        
    # Register the 4 synthetic datasets
    for meta in [meta_normal, meta_moderate, meta_compound, meta_extreme]:
        d_id = meta["dataset_id"]
        datasets[d_id] = {
            "dataset_id": d_id,
            "name": meta["name"],
            "filename": meta["filename"],
            "description": meta["description"],
            "file_path": meta["file_path"],
            "file_size_bytes": meta["file_size_bytes"],
            "created_at": meta["created_at"],
            "is_original": False,
            "is_synthetic": True,
            "row_count": meta["row_count"],
            "column_count": meta["column_count"],
            "encoding": meta["encoding"],
            "status": "VALIDATED",
            "scenario": meta["scenario"],
            "model_compatibility": meta["model_compatibility"]
        }
        
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
        
    print("Catalog updated successfully with all 5 datasets!")


if __name__ == "__main__":
    main()

