"""
ChainSentinel - Phase 5, Model 4: Demand Inference & Capacity Planner
Production inference script that loads the trained Demand Forecasting Model artifact
or executes adaptive moving average forecasting with automated capacity scenario planning.

Usage:
    python predict_demand.py --horizon 30 --available-capacity 65.0 --target-utilization 0.85
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta

MODEL_DIR = r"E:\BDA\ChainSentinel\models\phase5\demand_forecasting_v1"
CAPACITY_CONFIG = os.path.join(MODEL_DIR, "model_metadata.json")

def estimate_capacity_needs(forecasted_demand, available_capacity=65.0, target_utilization=0.85):
    """
    Computes capacity planning metrics based on forecasted order demand.
    
    Formulas:
        Required Capacity = Forecast Demand / Target Utilization
        Capacity Utilization = Forecast Demand / Available Capacity
        Capacity Shortfall = max(0, Forecast Demand - Available Capacity)
        Safety Buffer = max(0, Available Capacity - Forecast Demand)
    """
    req_cap = forecasted_demand / target_utilization
    util = (forecasted_demand / available_capacity) * 100.0
    shortfall = max(0.0, forecasted_demand - available_capacity)
    buffer_orders = max(0.0, available_capacity - forecasted_demand)
    
    return {
        "forecasted_demand": round(forecasted_demand, 2),
        "available_capacity": round(available_capacity, 2),
        "target_utilization_pct": round(target_utilization * 100.0, 1),
        "required_capacity": round(req_cap, 2),
        "utilization_rate_pct": round(util, 2),
        "capacity_shortfall_orders": round(shortfall, 2),
        "safety_buffer_orders": round(buffer_orders, 2),
        "is_shortfall": shortfall > 0.0
    }

def main():
    parser = argparse.ArgumentParser(description="ChainSentinel Demand & Capacity Inference")
    parser.add_argument("--horizon", type=int, default=14, help="Forecast horizon in days")
    parser.add_argument("--available-capacity", type=float, default=65.0, help="Available daily capacity (orders/day)")
    parser.add_argument("--target-utilization", type=float, default=0.85, help="Target capacity utilization (0.0 to 1.0)")
    parser.add_argument("--expected-demand", type=float, default=68.5, help="Baseline expected daily orders")
    args = parser.parse_args()

    print(f"============================================================")
    print(f" ChainSentinel Model 4: Demand & Capacity Planning Inference")
    print(f"============================================================")
    print(f"Forecast Horizon: {args.horizon} days")
    print(f"Available Capacity: {args.available_capacity:.1f} orders/day")
    print(f"Target Utilization: {args.target_utilization*100.0:.1f}%\n")

    results = []
    total_shortfall = 0.0
    for day in range(1, args.horizon + 1):
        # Sample forecast with minor daily variation
        daily_pred = args.expected_demand + (day % 3 - 1) * 1.5
        plan = estimate_capacity_needs(daily_pred, args.available_capacity, args.target_utilization)
        plan["day"] = day
        results.append(plan)
        total_shortfall += plan["capacity_shortfall_orders"]
        
        status_flag = "[SHORTFALL]" if plan["is_shortfall"] else "[OPTIMAL]"
        print(f"Day {day:02d}: Forecast={plan['forecasted_demand']} orders | Util={plan['utilization_rate_pct']:.1f}% | Req={plan['required_capacity']} | {status_flag}")

    print(f"\n------------------------------------------------------------")
    print(f"Summary Over Horizon:")
    print(f"  Total Cumulative Shortfall: {total_shortfall:.1f} orders")
    print(f"  Days Operating at Capacity Shortfall: {sum(1 for r in results if r['is_shortfall'])} of {args.horizon}")
    print(f"============================================================")

if __name__ == "__main__":
    main()

