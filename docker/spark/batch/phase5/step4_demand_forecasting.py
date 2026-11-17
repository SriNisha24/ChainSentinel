"""
ChainSentinel - Phase 5: Machine Learning and Predictive Analytics
Model 4: Demand Forecasting and Capacity Planning Analytics

Executes end-to-end demand aggregation, chronological time-series forecasting,
model evaluation against historical baselines, multi-echelon disaggregation
(Market, Top Regional Hubs, Shipping Modes), and scenario-based capacity requirement estimation.

Dataset Source:
  hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1
"""

import os
import sys
import json
import math
import logging
from datetime import datetime, timedelta

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, StringType, IntegerType, DateType
)

from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression, RandomForestRegressor, GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase5_Model4_DemandForecasting")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
OUTPUT_DIR = "/opt/spark-data/phase5_output"
LOCAL_MODEL_DIR = "/opt/spark-data/phase5_models/demand_forecasting_v1"
HDFS_MODEL_DIR = "hdfs://namenode:8020/chainsentinel/models/phase5/demand_forecasting_v1"

def calculate_metrics(y_true, y_pred):
    """Calculates MAE, RMSE, WAPE, and MAPE between two numeric lists."""
    n = len(y_true)
    if n == 0:
        return {"mae": 0.0, "rmse": 0.0, "wape": 0.0, "mape": 0.0}
    
    abs_errors = [abs(yt - yp) for yt, yp in zip(y_true, y_pred)]
    sq_errors = [(yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)]
    sum_true = sum(y_true)
    
    mae = sum(abs_errors) / n
    rmse = math.sqrt(sum(sq_errors) / n)
    wape = (sum(abs_errors) / sum_true * 100.0) if sum_true > 0 else 0.0
    mape = (sum(abs(yt - yp) / yt for yt, yp in zip(y_true, y_pred) if yt > 0) / n * 100.0)
    
    return {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "wape": round(wape, 2),
        "mape": round(mape, 2)
    }

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)

    spark = SparkSession.builder \
        .appName("ChainSentinel-Phase5-Model4-DemandForecasting") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading cleaned dataset from: {HDFS_DATASET}")
    df = spark.read.parquet(HDFS_DATASET)
    total_records = df.count()
    logger.info(f"Total dataset records: {total_records:,}")

    # Standardize order date
    df = df.withColumn("order_dt", F.to_date(F.col("order_date")))

    # =========================================================================
    # STEP 2: DEMAND AGGREGATION ACROSS MULTIPLE GRANULARITIES
    # =========================================================================
    logger.info("Aggregating daily network-level demand...")
    daily_df = df.groupBy("order_dt").agg(
        F.countDistinct("order_id").alias("distinct_orders"),
        F.count("order_id").alias("total_items"),
        F.round(F.sum("order_item_total"), 2).alias("net_revenue"),
        F.round(F.sum("order_profit_per_order"), 2).alias("net_profit")
    ).orderBy("order_dt")

    # Collect daily series for Python feature building and ML modeling
    daily_rows = daily_df.collect()
    logger.info(f"Aggregated {len(daily_rows)} continuous daily observations.")

    # Market level aggregation
    logger.info("Aggregating market-level demand...")
    market_df = df.groupBy("order_dt", "market").agg(
        F.countDistinct("order_id").alias("distinct_orders"),
        F.count("order_id").alias("total_items"),
        F.round(F.sum("order_item_total"), 2).alias("net_revenue")
    ).orderBy("order_dt", "market")
    market_rows = market_df.collect()

    # Top 5 Regional Hubs aggregation
    top_regions = ["Western Europe", "Central America", "South America", "Oceania", "Southeast Asia"]
    logger.info("Aggregating regional demand for top hubs...")
    regional_df = df.filter(F.col("order_region").isin(top_regions)).groupBy("order_dt", "order_region").agg(
        F.countDistinct("order_id").alias("distinct_orders"),
        F.count("order_id").alias("total_items"),
        F.round(F.sum("order_item_total"), 2).alias("net_revenue")
    ).orderBy("order_dt", "order_region")
    regional_rows = regional_df.collect()

    # Shipping Mode aggregation
    logger.info("Aggregating shipping mode demand...")
    shipping_df = df.groupBy("order_dt", "shipping_mode").agg(
        F.countDistinct("order_id").alias("distinct_orders"),
        F.count("order_id").alias("total_items"),
        F.round(F.sum("order_item_total"), 2).alias("net_revenue")
    ).orderBy("order_dt", "shipping_mode")
    shipping_rows = shipping_df.collect()

    # =========================================================================
    # STEP 3: TIME-SERIES FEATURE ENGINEERING (ZERO LEAKAGE)
    # =========================================================================
    # Build lag-based and rolling features chronologically
    records = []
    dates = [str(r["order_dt"]) for r in daily_rows]
    y_orders = [int(r["distinct_orders"]) for r in daily_rows]
    revs = [float(r["net_revenue"]) for r in daily_rows]
    profits = [float(r["net_profit"]) for r in daily_rows]
    items = [int(r["total_items"]) for r in daily_rows]

    for t in range(len(daily_rows)):
        dt_str = dates[t]
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d").date()
        
        # Need at least 14 days of history for lag 14 and rolling 14
        if t < 14:
            continue
            
        rec = {
            "order_dt": dt_str,
            "distinct_orders": y_orders[t],
            "total_items": items[t],
            "net_revenue": revs[t],
            "net_profit": profits[t],
            # Strict past lags
            "lag_1": float(y_orders[t-1]),
            "lag_2": float(y_orders[t-2]),
            "lag_3": float(y_orders[t-3]),
            "lag_7": float(y_orders[t-7]),
            "lag_14": float(y_orders[t-14]),
            # Strict backward rolling means (excluding current observation t)
            "ma_7": float(sum(y_orders[t-7:t]) / 7.0),
            "ma_14": float(sum(y_orders[t-14:t]) / 14.0),
            # Calendar features
            "day_of_week": float(dt_obj.isoweekday()), # 1=Mon, 7=Sun
            "day_of_month": float(dt_obj.day),
            "month": float(dt_obj.month)
        }
        records.append(rec)

    logger.info(f"Constructed {len(records)} feature rows with full 14-day history.")

    # Convert to Spark DataFrame for MLlib modeling
    feat_df = spark.createDataFrame(records)

    # Chronological Splits
    train_df = feat_df.filter(F.col("order_dt") < "2017-01-01").cache()
    val_df = feat_df.filter((F.col("order_dt") >= "2017-01-01") & (F.col("order_dt") < "2017-09-01")).cache()
    test_df = feat_df.filter(F.col("order_dt") >= "2017-09-01").cache()

    train_count = train_df.count()
    val_count = val_df.count()
    test_count = test_df.count()
    logger.info(f"Chronological Splits: Train={train_count} days, Val={val_count} days, Test={test_count} days")

    # Extract target and baseline predictions for Val and Test sets
    val_actual = [r["distinct_orders"] for r in val_df.select("distinct_orders").collect()]
    val_lag1 = [r["lag_1"] for r in val_df.select("lag_1").collect()]
    val_lag7 = [r["lag_7"] for r in val_df.select("lag_7").collect()]
    val_ma7 = [r["ma_7"] for r in val_df.select("ma_7").collect()]

    test_actual = [r["distinct_orders"] for r in test_df.select("distinct_orders").collect()]
    test_lag1 = [r["lag_1"] for r in test_df.select("lag_1").collect()]
    test_lag7 = [r["lag_7"] for r in test_df.select("lag_7").collect()]
    test_ma7 = [r["ma_7"] for r in test_df.select("ma_7").collect()]

    # Baselines evaluation
    metrics_summary = []

    # 1. Naive (Lag 1)
    val_m = calculate_metrics(val_actual, val_lag1)
    test_m = calculate_metrics(test_actual, test_lag1)
    metrics_summary.append({
        "model": "Naive Baseline (Lag 1)",
        "model_type": "Baseline",
        "val_mae": val_m["mae"], "val_rmse": val_m["rmse"], "val_wape": val_m["wape"], "val_mape": val_m["mape"],
        "test_mae": test_m["mae"], "test_rmse": test_m["rmse"], "test_wape": test_m["wape"], "test_mape": test_m["mape"]
    })

    # 2. Seasonal Naive (Lag 7)
    val_m = calculate_metrics(val_actual, val_lag7)
    test_m = calculate_metrics(test_actual, test_lag7)
    metrics_summary.append({
        "model": "Seasonal Naive (Lag 7)",
        "model_type": "Baseline",
        "val_mae": val_m["mae"], "val_rmse": val_m["rmse"], "val_wape": val_m["wape"], "val_mape": val_m["mape"],
        "test_mae": test_m["mae"], "test_rmse": test_m["rmse"], "test_wape": test_m["wape"], "test_mape": test_m["mape"]
    })

    # 3. Moving Average (MA 7)
    val_m = calculate_metrics(val_actual, val_ma7)
    test_m = calculate_metrics(test_actual, test_ma7)
    metrics_summary.append({
        "model": "Moving Average (MA 7)",
        "model_type": "Baseline",
        "val_mae": val_m["mae"], "val_rmse": val_m["rmse"], "val_wape": val_m["wape"], "val_mape": val_m["mape"],
        "test_mae": test_m["mae"], "test_rmse": test_m["rmse"], "test_wape": test_m["wape"], "test_mape": test_m["mape"]
    })

    # ML Pipeline Setup
    feature_cols = ["lag_1", "lag_2", "lag_3", "lag_7", "lag_14", "ma_7", "ma_14", "day_of_week", "day_of_month", "month"]
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")

    # 4. Spark ML Linear Regression
    logger.info("Training Linear Regression...")
    lr = LinearRegression(featuresCol="features", labelCol="distinct_orders", regParam=0.1)
    pipeline_lr = Pipeline(stages=[assembler, lr])
    model_lr = pipeline_lr.fit(train_df)
    
    val_pred_lr = [r["prediction"] for r in model_lr.transform(val_df).select("prediction").collect()]
    test_pred_lr = [r["prediction"] for r in model_lr.transform(test_df).select("prediction").collect()]
    val_m = calculate_metrics(val_actual, val_pred_lr)
    test_m = calculate_metrics(test_actual, test_pred_lr)
    metrics_summary.append({
        "model": "Linear Regression (Lags+MA)",
        "model_type": "Spark ML",
        "val_mae": val_m["mae"], "val_rmse": val_m["rmse"], "val_wape": val_m["wape"], "val_mape": val_m["mape"],
        "test_mae": test_m["mae"], "test_rmse": test_m["rmse"], "test_wape": test_m["wape"], "test_mape": test_m["mape"]
    })

    # 5. Spark ML Random Forest Regressor
    logger.info("Training Random Forest Regressor...")
    rf = RandomForestRegressor(featuresCol="features", labelCol="distinct_orders", numTrees=50, maxDepth=5, seed=42)
    pipeline_rf = Pipeline(stages=[assembler, rf])
    model_rf = pipeline_rf.fit(train_df)
    
    val_pred_rf = [r["prediction"] for r in model_rf.transform(val_df).select("prediction").collect()]
    test_pred_rf = [r["prediction"] for r in model_rf.transform(test_df).select("prediction").collect()]
    val_m = calculate_metrics(val_actual, val_pred_rf)
    test_m = calculate_metrics(test_actual, test_pred_rf)
    metrics_summary.append({
        "model": "Random Forest Regressor",
        "model_type": "Spark ML",
        "val_mae": val_m["mae"], "val_rmse": val_m["rmse"], "val_wape": val_m["wape"], "val_mape": val_m["mape"],
        "test_mae": test_m["mae"], "test_rmse": test_m["rmse"], "test_wape": test_m["wape"], "test_mape": test_m["mape"]
    })

    # 6. Spark ML GBT Regressor
    logger.info("Training GBT Regressor...")
    gbt = GBTRegressor(featuresCol="features", labelCol="distinct_orders", maxDepth=4, maxIter=30, seed=42)
    pipeline_gbt = Pipeline(stages=[assembler, gbt])
    model_gbt = pipeline_gbt.fit(train_df)
    
    val_pred_gbt = [r["prediction"] for r in model_gbt.transform(val_df).select("prediction").collect()]
    test_pred_gbt = [r["prediction"] for r in model_gbt.transform(test_df).select("prediction").collect()]
    val_m = calculate_metrics(val_actual, val_pred_gbt)
    test_m = calculate_metrics(test_actual, test_pred_gbt)
    metrics_summary.append({
        "model": "GBT Regressor",
        "model_type": "Spark ML",
        "val_mae": val_m["mae"], "val_rmse": val_m["rmse"], "val_wape": val_m["wape"], "val_mape": val_m["mape"],
        "test_mae": test_m["mae"], "test_rmse": test_m["rmse"], "test_wape": test_m["wape"], "test_mape": test_m["mape"]
    })

    # Export Model Evaluation Metrics CSV
    metrics_csv_path = os.path.join(OUTPUT_DIR, "step4_forecast_metrics.csv")
    with open(metrics_csv_path, "w") as f:
        f.write("model,model_type,val_mae,val_rmse,val_wape,val_mape,test_mae,test_rmse,test_wape,test_mape\n")
        for m in metrics_summary:
            f.write(f'"{m["model"]}","{m["model_type"]}",{m["val_mae"]},{m["val_rmse"]},{m["val_wape"]},{m["val_mape"]},{m["test_mae"]},{m["test_rmse"]},{m["test_wape"]},{m["test_mape"]}\n')
    logger.info(f"Saved forecast metrics to: {metrics_csv_path}")

    # Select Best Performing Model on Validation Set (MAE)
    best_model_name = min(metrics_summary, key=lambda x: x["val_mae"])["model"]
    logger.info(f"Best model based on Validation MAE: {best_model_name}")

    # Use Moving Average / GBT for final test set and scenario forecasts
    # Calculate residuals and 95% empirical prediction intervals on test set
    test_dates = [r["order_dt"] for r in test_df.select("order_dt").collect()]
    test_preds = test_pred_lr  # Linear regression or best model
    # Residuals on validation set for prediction intervals
    val_residuals = [act - pred for act, pred in zip(val_actual, val_pred_lr)]
    val_res_std = math.sqrt(sum(r**2 for r in val_residuals) / len(val_residuals))
    pi_margin = 1.96 * val_res_std

    # =========================================================================
    # STEP 4: OVERALL DEMAND FORECAST CSV
    # =========================================================================
    overall_forecast_csv = os.path.join(OUTPUT_DIR, "step4_overall_demand_forecast.csv")
    with open(overall_forecast_csv, "w") as f:
        f.write("order_date,actual_orders,predicted_orders,residual,pi_lower_95,pi_upper_95\n")
        for dt, act, pred in zip(test_dates, test_actual, test_preds):
            pred_val = round(pred, 2)
            res = round(act - pred_val, 2)
            pi_low = round(max(0, pred_val - pi_margin), 2)
            pi_high = round(pred_val + pi_margin, 2)
            f.write(f"{dt},{act},{pred_val},{res},{pi_low},{pi_high}\n")
    logger.info(f"Saved overall demand forecast to: {overall_forecast_csv}")

    # =========================================================================
    # STEP 4.2: MULTI-ECHELON DISAGGREGATED FORECASTS (Test Horizon)
    # =========================================================================
    # Market-Level Test Period Forecasts
    logger.info("Generating Market-Level Forecasts...")
    market_forecast_csv = os.path.join(OUTPUT_DIR, "step4_market_demand_forecast.csv")
    market_historical_shares = {
        "Europe": 0.2823,
        "Pacific Asia": 0.2673,
        "LATAM": 0.2613,
        "USCA": 0.1305,
        "Africa": 0.0586
    }
    # Group actual test demand by market
    test_market_actuals = {}
    for r in market_rows:
        dt = str(r["order_dt"])
        if dt >= "2017-09-01":
            mkt = r["market"]
            test_market_actuals[(dt, mkt)] = int(r["distinct_orders"])

    with open(market_forecast_csv, "w") as f:
        f.write("order_date,market,actual_orders,predicted_orders,absolute_error\n")
        for dt, pred in zip(test_dates, test_preds):
            for mkt, share in market_historical_shares.items():
                mkt_pred = round(pred * share, 2)
                mkt_act = test_market_actuals.get((dt, mkt), 0)
                err = round(abs(mkt_act - mkt_pred), 2)
                f.write(f"{dt},\"{mkt}\",{mkt_act},{mkt_pred},{err}\n")
    logger.info(f"Saved market demand forecast to: {market_forecast_csv}")

    # Top 5 Regional Forecasts
    logger.info("Generating Top Regional Forecasts...")
    regional_forecast_csv = os.path.join(OUTPUT_DIR, "step4_regional_demand_forecast.csv")
    regional_historical_shares = {
        "Western Europe": 0.1522,
        "Central America": 0.1429,
        "South America": 0.0757,
        "Oceania": 0.0663,
        "Southeast Asia": 0.0662
    }
    test_regional_actuals = {}
    for r in regional_rows:
        dt = str(r["order_dt"])
        if dt >= "2017-09-01":
            reg = r["order_region"]
            test_regional_actuals[(dt, reg)] = int(r["distinct_orders"])

    with open(regional_forecast_csv, "w") as f:
        f.write("order_date,order_region,actual_orders,predicted_orders,absolute_error\n")
        for dt, pred in zip(test_dates, test_preds):
            for reg, share in regional_historical_shares.items():
                reg_pred = round(pred * share, 2)
                reg_act = test_regional_actuals.get((dt, reg), 0)
                err = round(abs(reg_act - reg_pred), 2)
                f.write(f"{dt},\"{reg}\",{reg_act},{reg_pred},{err}\n")
    logger.info(f"Saved regional demand forecast to: {regional_forecast_csv}")

    # Shipping Mode Forecasts
    logger.info("Generating Shipping Mode Forecasts...")
    shipping_forecast_csv = os.path.join(OUTPUT_DIR, "step4_shipping_mode_forecast.csv")
    shipping_historical_shares = {
        "Standard Class": 0.5981,
        "Second Class": 0.1943,
        "First Class": 0.1533,
        "Same Day": 0.0543
    }
    test_shipping_actuals = {}
    for r in shipping_rows:
        dt = str(r["order_dt"])
        if dt >= "2017-09-01":
            mode = r["shipping_mode"]
            test_shipping_actuals[(dt, mode)] = int(r["distinct_orders"])

    with open(shipping_forecast_csv, "w") as f:
        f.write("order_date,shipping_mode,actual_orders,predicted_orders,absolute_error\n")
        for dt, pred in zip(test_dates, test_preds):
            for mode, share in shipping_historical_shares.items():
                mode_pred = round(pred * share, 2)
                mode_act = test_shipping_actuals.get((dt, mode), 0)
                err = round(abs(mode_act - mode_pred), 2)
                f.write(f"{dt},\"{mode}\",{mode_act},{mode_pred},{err}\n")
    logger.info(f"Saved shipping mode forecast to: {shipping_forecast_csv}")

    # =========================================================================
    # STEPS 5 & 6: TRANSPARENT CAPACITY ESTIMATION & SCENARIO ANALYSIS
    # =========================================================================
    logger.info("Evaluating Capacity Planning Scenarios...")
    scenarios = [
        {
            "scenario_id": "SCENARIO_1_NORMAL_OPERATIONS",
            "name": "Normal Operations Baseline",
            "demand_multiplier": 1.0,
            "target_utilization": 0.85,
            "available_capacity": 65.0,
            "description": "Baseline forecasted demand under standard 65 orders/day fulfillment capacity."
        },
        {
            "scenario_id": "SCENARIO_2_DEMAND_SURGE",
            "name": "Demand Surge (+20% Growth)",
            "demand_multiplier": 1.20,
            "target_utilization": 0.85,
            "available_capacity": 65.0,
            "description": "20% demand growth from promotional campaigns against normal capacity."
        },
        {
            "scenario_id": "SCENARIO_3_PEAK_SEASON",
            "name": "Peak Season (+35% Spike)",
            "demand_multiplier": 1.35,
            "target_utilization": 0.90,
            "available_capacity": 65.0,
            "description": "Severe holiday/seasonal peak surge (+35%) with relaxed 90% target utilization."
        },
        {
            "scenario_id": "SCENARIO_4_CONSTRAINED_CAPACITY",
            "name": "Capacity Constraint (-25% Available)",
            "demand_multiplier": 1.0,
            "target_utilization": 0.85,
            "available_capacity": 48.75,
            "description": "Operational bottlenecks, labor shortages, or maintenance causing 25% capacity reduction."
        }
    ]

    scenario_results = []
    daily_scenario_records = []

    for sc in scenarios:
        mult = sc["demand_multiplier"]
        target_u = sc["target_utilization"]
        c_avail = sc["available_capacity"]

        demands = [p * mult for p in test_preds]
        req_capacities = [d / target_u for d in demands]
        utilizations = [d / c_avail for d in demands]
        shortfalls = [max(0.0, d - c_avail) for d in demands]
        add_reqs = [max(0.0, rc - c_avail) for rc in req_capacities]
        buffers = [max(0.0, c_avail - d) for d in demands]

        days_shortfall = sum(1 for s in shortfalls if s > 0.0)
        total_shortfall_vol = sum(shortfalls)
        max_shortfall = max(shortfalls)
        avg_demand = sum(demands) / len(demands)
        avg_req_cap = sum(req_capacities) / len(req_capacities)
        avg_util = (sum(utilizations) / len(utilizations)) * 100.0
        avg_add_req = sum(add_reqs) / len(add_reqs)
        avg_buffer = sum(buffers) / len(buffers)

        res = {
            "scenario_id": sc["scenario_id"],
            "name": sc["name"],
            "demand_multiplier": mult,
            "target_utilization": target_u,
            "available_capacity": c_avail,
            "avg_daily_demand": round(avg_demand, 2),
            "avg_required_capacity": round(avg_req_cap, 2),
            "avg_capacity_utilization_pct": round(avg_util, 2),
            "days_with_shortfall": days_shortfall,
            "pct_days_with_shortfall": round(days_shortfall / len(demands) * 100.0, 2),
            "total_unmet_order_volume": round(total_shortfall_vol, 2),
            "max_daily_shortfall": round(max_shortfall, 2),
            "avg_additional_capacity_needed": round(avg_add_req, 2),
            "avg_safety_buffer_orders": round(avg_buffer, 2),
            "description": sc["description"]
        }
        scenario_results.append(res)

        # Store daily records for CSV export
        for dt, d, rc, u, s in zip(test_dates, demands, req_capacities, utilizations, shortfalls):
            daily_scenario_records.append({
                "order_date": dt,
                "scenario_id": sc["scenario_id"],
                "forecast_demand": round(d, 2),
                "available_capacity": c_avail,
                "required_capacity": round(rc, 2),
                "utilization_rate": round(u, 4),
                "capacity_shortfall": round(s, 2)
            })

    # Save Capacity Scenarios CSV
    capacity_csv_path = os.path.join(OUTPUT_DIR, "step4_capacity_scenarios.csv")
    with open(capacity_csv_path, "w") as f:
        f.write("order_date,scenario_id,forecast_demand,available_capacity,required_capacity,utilization_rate,capacity_shortfall\n")
        for r in daily_scenario_records:
            f.write(f'{r["order_date"]},"{r["scenario_id"]}",{r["forecast_demand"]},{r["available_capacity"]},{r["required_capacity"]},{r["utilization_rate"]},{r["capacity_shortfall"]}\n')
    logger.info(f"Saved capacity scenarios CSV to: {capacity_csv_path}")

    # Save Capacity Summary JSON
    capacity_json_path = os.path.join(OUTPUT_DIR, "step4_capacity_summary.json")
    with open(capacity_json_path, "w") as f:
        json.dump({
            "model_metadata": {
                "component": "Model 4: Demand Forecasting and Capacity Planning Analytics",
                "training_period": "2015-01-01 to 2016-12-31",
                "validation_period": "2017-01-01 to 2017-08-31",
                "test_period": "2017-09-01 to 2018-01-31",
                "test_horizon_days": len(test_dates),
                "timestamp": datetime.now().isoformat()
            },
            "forecasting_performance": metrics_summary,
            "best_forecasting_model": best_model_name,
            "capacity_scenarios_summary": scenario_results
        }, f, indent=2)
    logger.info(f"Saved capacity summary JSON to: {capacity_json_path}")

    # Save Spark ML Model Artifact
    logger.info(f"Exporting model artifact to: {LOCAL_MODEL_DIR}")
    model_lr.write().overwrite().save(os.path.join(LOCAL_MODEL_DIR, "spark_model"))
    
    # Save Model metadata
    with open(os.path.join(LOCAL_MODEL_DIR, "model_metadata.json"), "w") as f:
        json.dump({
            "model_type": "LinearRegression",
            "feature_columns": feature_cols,
            "regParam": 0.1,
            "input_dataset": HDFS_DATASET,
            "training_samples": train_count,
            "validation_samples": val_count,
            "test_samples": test_count
        }, f, indent=2)
    logger.info("Model artifact and metadata saved successfully.")

    spark.stop()
    logger.info("Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()

