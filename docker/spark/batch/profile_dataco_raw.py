"""
ChainSentinel - Big Data Analytics Project
Dataset Inspection and Profiling Tool (Phase 1)

This script performs memory-efficient, chunked profiling of raw datasets in
E:\BDA\ChainSentinel\data\raw (or /opt/spark-data/raw inside Docker).
Does not modify any source data.
"""

import os
import sys
import json
import logging
from collections import defaultdict
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("ChainSentinelProfiler")


def get_data_dir():
    # Check common paths (Windows host vs Spark container)
    candidates = [
        r"E:\BDA\ChainSentinel\data\raw",
        "/opt/spark-data/raw",
        "./data/raw",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Could not locate raw dataset directory.")


def inspect_dataco_main(data_dir, chunksize=25000):
    filepath = os.path.join(data_dir, "DataCoSupplyChainDataset.csv")
    if not os.path.exists(filepath):
        logger.error(f"Missing main dataset: {filepath}")
        return None

    file_size_bytes = os.path.getsize(filepath)
    file_size_mb = file_size_bytes / (1024 * 1024)
    logger.info(f"Profiling DataCoSupplyChainDataset.csv ({file_size_mb:.2f} MB)...")

    # Chunked scan
    total_rows = 0
    null_counts = None
    dtypes = None
    cols = None
    order_item_ids = set()
    order_ids = set()
    customer_ids = set()
    
    delivery_status_counts = defaultdict(int)
    late_risk_counts = defaultdict(int)
    shipping_mode_counts = defaultdict(int)
    type_counts = defaultdict(int)
    order_status_counts = defaultdict(int)
    market_counts = defaultdict(int)

    # Numerical accumulators
    num_cols = [
        'Days for shipping (real)', 'Days for shipment (scheduled)',
        'Benefit per order', 'Sales per customer', 'Late_delivery_risk',
        'Order Item Discount', 'Order Item Discount Rate',
        'Order Item Product Price', 'Order Item Profit Ratio',
        'Order Item Quantity', 'Sales', 'Product Price'
    ]

    for chunk in pd.read_csv(filepath, encoding="latin1", chunksize=chunksize, low_memory=False):
        if cols is None:
            cols = chunk.columns.tolist()
            null_counts = chunk.isnull().sum()
            dtypes = {col: str(dtype) for col, dtype in chunk.dtypes.items()}
        else:
            null_counts += chunk.isnull().sum()

        total_rows += len(chunk)
        order_item_ids.update(chunk["Order Item Id"].tolist())
        order_ids.update(chunk["Order Id"].tolist())
        customer_ids.update(chunk["Customer Id"].tolist())

        for k, v in chunk["Delivery Status"].value_counts().items():
            delivery_status_counts[k] += int(v)
        for k, v in chunk["Late_delivery_risk"].value_counts().items():
            late_risk_counts[int(k)] += int(v)
        for k, v in chunk["Shipping Mode"].value_counts().items():
            shipping_mode_counts[k] += int(v)
        for k, v in chunk["Type"].value_counts().items():
            type_counts[k] += int(v)
        for k, v in chunk["Order Status"].value_counts().items():
            order_status_counts[k] += int(v)
        for k, v in chunk["Market"].value_counts().items():
            market_counts[k] += int(v)

    # Calculate duplicate Order Item IDs
    duplicate_item_ids = total_rows - len(order_item_ids)

    # Numerical describe on subset (memory-friendly)
    num_df = pd.read_csv(filepath, encoding="latin1", usecols=num_cols)
    stats_desc = num_df.describe().to_dict()

    return {
        "file_name": "DataCoSupplyChainDataset.csv",
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
        "total_rows": total_rows,
        "total_columns": len(cols),
        "columns": cols,
        "dtypes": dtypes,
        "null_counts": {k: int(v) for k, v in null_counts.items() if v > 0},
        "null_percentages": {k: round((v / total_rows) * 100, 2) for k, v in null_counts.items() if v > 0},
        "unique_order_item_ids": len(order_item_ids),
        "duplicate_order_item_ids": duplicate_item_ids,
        "unique_orders": len(order_ids),
        "unique_customers": len(customer_ids),
        "delivery_status_distribution": dict(delivery_status_counts),
        "late_delivery_risk_distribution": dict(late_risk_counts),
        "shipping_mode_distribution": dict(shipping_mode_counts),
        "type_distribution": dict(type_counts),
        "order_status_distribution": dict(order_status_counts),
        "market_distribution": dict(market_counts),
        "descriptive_stats": stats_desc,
    }


def inspect_access_logs(data_dir):
    filepath = os.path.join(data_dir, "tokenized_access_logs.csv")
    if not os.path.exists(filepath):
        logger.warning(f"Supporting file not found: {filepath}")
        return None

    file_size_bytes = os.path.getsize(filepath)
    file_size_mb = file_size_bytes / (1024 * 1024)
    logger.info(f"Profiling tokenized_access_logs.csv ({file_size_mb:.2f} MB)...")

    df = pd.read_csv(filepath)
    dates = pd.to_datetime(df["Date"], format="%m/%d/%Y %H:%M", errors="coerce")

    return {
        "file_name": "tokenized_access_logs.csv",
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": df.columns.tolist(),
        "null_counts": {k: int(v) for k, v in df.isnull().sum().items() if v > 0},
        "unique_products": int(df["Product"].nunique()),
        "unique_categories": int(df["Category"].nunique()),
        "unique_departments": int(df["Department"].nunique()),
        "unique_ips": int(df["ip"].nunique()),
        "unique_urls": int(df["url"].nunique()),
        "date_min": str(dates.min()),
        "date_max": str(dates.max()),
        "duplicate_rows": int(df.duplicated().sum()),
        "top_departments": df["Department"].value_counts().head(5).to_dict(),
        "top_categories": df["Category"].value_counts().head(5).to_dict(),
    }


def inspect_metadata_file(data_dir):
    filepath = os.path.join(data_dir, "DescriptionDataCoSupplyChain.csv")
    if not os.path.exists(filepath):
        return None
    df = pd.read_csv(filepath, encoding="latin1")
    return {
        "file_name": "DescriptionDataCoSupplyChain.csv",
        "file_size_bytes": os.path.getsize(filepath),
        "fields_described": len(df),
        "columns": df.columns.tolist(),
    }


def run_profiling():
    data_dir = get_data_dir()
    logger.info(f"Profiling raw datasets located at: {data_dir}")

    report = {
        "metadata": inspect_metadata_file(data_dir),
        "dataco_main": inspect_dataco_main(data_dir),
        "access_logs": inspect_access_logs(data_dir),
    }

    output_path = os.path.join(data_dir, "..", "..", "reports", "dataset_profile_summary.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Profiling completed successfully. Summary saved to: {output_path}")


if __name__ == "__main__":
    run_profiling()

