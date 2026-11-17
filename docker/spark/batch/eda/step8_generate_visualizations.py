"""
ChainSentinel - Phase 3 EDA: Step 8
Visualizations and Master EDA Summary Compiler

Renders publication-grade PNG visualizations using Matplotlib & Seaborn,
compiles all step metrics into eda_summary.json, and stores all artifacts
in E:\\BDA\\ChainSentinel\\reports\\eda\\
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

REPORTS_DIR = r"E:\BDA\ChainSentinel\reports\eda"
os.makedirs(REPORTS_DIR, exist_ok=True)

# Set high-resolution aesthetics
sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams.update({
    "figure.autolayout": True,
    "figure.dpi": 300,
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.labelweight": "bold",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9
})

def plot_delivery_status():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step3_delivery_status.csv"))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    colors = ["#e74c3c", "#2ecc71", "#3498db", "#95a5a6"]
    sns.barplot(x="delivery_status", y="count", data=df, palette=colors, ax=ax1)
    ax1.set_title("Order Count by Delivery Status")
    ax1.set_xlabel("Delivery Status")
    ax1.set_ylabel("Number of Orders")
    for p in ax1.patches:
        ax1.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="baseline", fontsize=9, xytext=(0, 4), textcoords="offset points")

    ax2.pie(df["count"], labels=df["delivery_status"], autopct="%1.1f%%", colors=colors, startangle=140,
            explode=[0.05, 0, 0, 0], shadow=True)
    ax2.set_title("Delivery Status Proportion (%)")

    plt.suptitle("ChainSentinel — Delivery Status & Disruption Distribution", fontsize=15, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart1_delivery_status_distribution.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_shipping_mode_delays():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step3_shipping_mode_delays.csv"))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    sns.barplot(x="shipping_mode", y="delay_rate_pct", data=df, palette="Reds_r", ax=ax1)
    ax1.set_title("Delay Rate by Shipping Mode (%)")
    ax1.set_xlabel("Shipping Mode")
    ax1.set_ylabel("Delay Rate (%)")
    ax1.set_ylim(0, 105)
    for p in ax1.patches:
        ax1.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="baseline", fontsize=9, xytext=(0, 4), textcoords="offset points")

    x = np.arange(len(df["shipping_mode"]))
    width = 0.35
    ax2.bar(x - width/2, df["avg_scheduled_days"], width, label="Scheduled SLA Days", color="#3498db")
    ax2.bar(x + width/2, df["avg_real_days"], width, label="Actual Real Days", color="#e67e22")
    ax2.set_title("Scheduled SLA vs Actual Fulfillment Days")
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["shipping_mode"])
    ax2.set_ylabel("Days")
    ax2.legend()
    for i in range(len(df)):
        ax2.annotate(f"{df['avg_scheduled_days'][i]:.1f}", (x[i] - width/2, df['avg_scheduled_days'][i] + 0.1), ha="center", fontsize=8)
        ax2.annotate(f"{df['avg_real_days'][i]:.1f}", (x[i] + width/2, df['avg_real_days'][i] + 0.1), ha="center", fontsize=8)

    plt.suptitle("ChainSentinel — Shipping Mode Disruption Analysis", fontsize=15, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart2_delay_rates_by_shipping_mode.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_market_performance():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step4_market_performance.csv"))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    sns.barplot(x="market", y="total_orders", data=df, palette="Blues_r", ax=ax1)
    ax1.set_title("Total Order Volume by Global Destination Market")
    ax1.set_xlabel("Market")
    ax1.set_ylabel("Total Orders")
    for p in ax1.patches:
        ax1.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="baseline", fontsize=9, xytext=(0, 4), textcoords="offset points")

    sns.barplot(x="market", y="delay_rate_pct", data=df, palette="Oranges_r", ax=ax2)
    ax2.set_title("Delay Rate by Destination Market (%)")
    ax2.set_xlabel("Market")
    ax2.set_ylabel("Delay Rate (%)")
    ax2.set_ylim(0, 70)
    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="baseline", fontsize=9, xytext=(0, 4), textcoords="offset points")

    plt.suptitle("ChainSentinel — Geographic Market Performance & Uniformity", fontsize=15, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart3_delay_rates_by_market.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_monthly_order_trends():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step3_monthly_delays.csv"))
    df["year_month"] = df["order_year"].astype(str) + "-" + df["order_month"].astype(str).str.zfill(2)

    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.plot(df["year_month"], df["total_orders"], marker="o", color="#2980b9", linewidth=2, label="Monthly Order Volume")
    ax1.set_xlabel("Order Year-Month")
    ax1.set_ylabel("Order Count", color="#2980b9")
    ax1.tick_params(axis="y", labelcolor="#2980b9")
    plt.xticks(rotation=45, ha="right")

    ax2 = ax1.twinx()
    ax2.plot(df["year_month"], df["delay_rate_pct"], marker="s", color="#e74c3c", linewidth=2, linestyle="--", label="Delay Rate (%)")
    ax2.set_ylabel("Delay Rate (%)", color="#e74c3c")
    ax2.tick_params(axis="y", labelcolor="#e74c3c")
    ax2.set_ylim(40, 70)

    plt.title("ChainSentinel — Longitudinal Monthly Order Volume & Disruption Rates (2015–2018)", fontsize=14, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart4_monthly_order_and_delay_trends.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_sales_and_profit_trends():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step6_monthly_financials.csv"))
    df["year_month"] = df["order_year"].astype(str) + "-" + df["order_month"].astype(str).str.zfill(2)

    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.bar(df["year_month"], df["monthly_net_sales"] / 1000.0, color="#3498db", alpha=0.7, label="Net Sales ($K)")
    ax1.set_xlabel("Order Year-Month")
    ax1.set_ylabel("Monthly Net Sales ($ in Thousands)", color="#2980b9")
    ax1.tick_params(axis="y", labelcolor="#2980b9")
    plt.xticks(rotation=45, ha="right")

    ax2 = ax1.twinx()
    ax2.plot(df["year_month"], df["monthly_profit"] / 1000.0, marker="o", color="#27ae60", linewidth=2.5, label="Profit ($K)")
    ax2.set_ylabel("Monthly Operating Profit ($ in Thousands)", color="#27ae60")
    ax2.tick_params(axis="y", labelcolor="#27ae60")

    plt.title("ChainSentinel — Monthly Revenue & Operating Profit Trajectory", fontsize=14, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart5_sales_and_profit_trends.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_category_distribution():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step5_category_performance.csv"))
    top15 = df.head(15).copy()
    top15["cat_label"] = top15["category_name"] + " (ID:" + top15["category_id"].astype(str) + ")"

    plt.figure(figsize=(12, 7))
    sns.barplot(x="total_orders", y="cat_label", data=top15, palette="viridis")
    plt.title("ChainSentinel — Top 15 Product Categories by Order Volume", fontsize=14, weight="bold")
    plt.xlabel("Total Order Count")
    plt.ylabel("Category (with Distinct ID)")
    for p in plt.gca().patches:
        plt.gca().annotate(f"{int(p.get_width()):,}", (p.get_width(), p.get_y() + p.get_height() / 2.),
                           ha="left", va="center", fontsize=8.5, xytext=(4, 0), textcoords="offset points")

    out_path = os.path.join(REPORTS_DIR, "chart6_product_category_distribution.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_customer_segments():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step5_customer_segments.csv"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    colors = ["#34495e", "#16a085", "#d35400"]

    ax1.pie(df["total_orders"], labels=df["customer_segment"], autopct="%1.1f%%", colors=colors, startangle=140, shadow=True)
    ax1.set_title("Customer Segment Share by Order Volume")

    sns.barplot(x="customer_segment", y="avg_order_value", data=df, palette=colors, ax=ax2)
    ax2.set_title("Average Order Value by Segment ($)")
    ax2.set_xlabel("Customer Segment")
    ax2.set_ylabel("Avg Order Value ($)")
    for p in ax2.patches:
        ax2.annotate(f"${p.get_height():.2f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="baseline", fontsize=9, xytext=(0, 4), textcoords="offset points")

    plt.suptitle("ChainSentinel — Customer Segmentation & Spending Profiles", fontsize=15, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart7_customer_segment_distribution.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_correlation_heatmap():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step7_correlation_matrix.csv"), index_col="feature")

    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(df, dtype=bool))
    sns.heatmap(df, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1.0, vmax=1.0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, mask=mask)
    plt.title("ChainSentinel — Numerical Feature Correlation Heatmap", fontsize=14, weight="bold")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)

    out_path = os.path.join(REPORTS_DIR, "chart8_correlation_heatmap.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_regional_performance():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step4_region_performance.csv"))

    plt.figure(figsize=(12, 8))
    sns.barplot(x="total_orders", y="order_region", data=df, palette="Spectral")
    plt.title("ChainSentinel — Order Volume across All 23 Global Delivery Regions", fontsize=14, weight="bold")
    plt.xlabel("Total Order Count")
    plt.ylabel("Destination Region")
    for p in plt.gca().patches:
        plt.gca().annotate(f"{int(p.get_width()):,}", (p.get_width(), p.get_y() + p.get_height() / 2.),
                           ha="left", va="center", fontsize=8, xytext=(4, 0), textcoords="offset points")

    out_path = os.path.join(REPORTS_DIR, "chart9_regional_delivery_performance.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_scheduled_vs_actual_days():
    with open(os.path.join(REPORTS_DIR, "step3_summary.json"), "r") as f:
        data = json.load(f)
    crosstab_raw = data["scheduled_vs_actual_crosstab"]

    ct_df = pd.DataFrame(crosstab_raw)
    ct_df = ct_df.set_index("days_for_shipment_scheduled_days_for_shipping_real")
    ct_df.index.name = "Scheduled SLA Days"
    ct_df.columns.name = "Actual Real Days"
    for col in ct_df.columns:
        ct_df[col] = pd.to_numeric(ct_df[col])

    plt.figure(figsize=(9, 6))
    sns.heatmap(ct_df, annot=True, fmt=",d", cmap="YlOrRd", cbar_kws={"label": "Order Count"})
    plt.title("ChainSentinel — Scheduled SLA vs Actual Real Days Matrix", fontsize=14, weight="bold")
    plt.xlabel("Actual Real Shipping Days")
    plt.ylabel("Scheduled Target Days (SLA)")

    out_path = os.path.join(REPORTS_DIR, "chart10_scheduled_vs_actual_shipping_days.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_discount_vs_profitability():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step6_discount_analysis.csv"))

    fig, ax1 = plt.subplots(figsize=(11, 5))
    ax1.plot(df["discount_rate"] * 100, df["avg_profit"], marker="o", color="#27ae60", linewidth=2.5, label="Average Profit ($)")
    ax1.set_xlabel("Discount Rate (%)")
    ax1.set_ylabel("Average Profit per Order ($)", color="#27ae60")
    ax1.tick_params(axis="y", labelcolor="#27ae60")

    ax2 = ax1.twinx()
    ax2.plot(df["discount_rate"] * 100, df["loss_rate_pct"], marker="s", color="#c0392b", linewidth=2.5, linestyle="--", label="Loss Order Rate (%)")
    ax2.set_ylabel("Loss Order Percentage (%)", color="#c0392b")
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax2.set_ylim(0, 30)

    plt.title("ChainSentinel — Discount Rate Impact on Profitability & Loss Incidence", fontsize=14, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart11_discount_vs_profitability.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_payment_type_risk():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step6_payment_analysis.csv"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    colors = ["#2980b9", "#8e44ad", "#f39c12", "#27ae60"]

    sns.barplot(x="payment_type", y="total_orders", data=df, palette=colors, ax=ax1)
    ax1.set_title("Order Volume by Payment Method")
    ax1.set_xlabel("Payment Type")
    ax1.set_ylabel("Order Count")
    for p in ax1.patches:
        ax1.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="baseline", fontsize=9, xytext=(0, 4), textcoords="offset points")

    x = np.arange(len(df["payment_type"]))
    width = 0.35
    ax2.bar(x - width/2, df["delay_rate_pct"], width, label="Delay Rate (%)", color="#e74c3c")
    ax2.bar(x + width/2, df["cancel_rate_pct"], width, label="Cancellation Rate (%)", color="#34495e")
    ax2.set_title("Risk Profile: Delay Rate vs Cancellation Rate (%)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["payment_type"])
    ax2.set_ylabel("Percentage (%)")
    ax2.legend()
    for i in range(len(df)):
        ax2.annotate(f"{df['delay_rate_pct'][i]:.1f}%", (x[i] - width/2, df['delay_rate_pct'][i] + 0.5), ha="center", fontsize=8)
        ax2.annotate(f"{df['cancel_rate_pct'][i]:.1f}%", (x[i] + width/2, df['cancel_rate_pct'][i] + 0.5), ha="center", fontsize=8)

    plt.suptitle("ChainSentinel — Payment Method Disruption & Cancellation Profiles", fontsize=15, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart12_payment_type_risk_profile.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def compile_master_summary():
    master = {
        "project": "ChainSentinel",
        "phase": 3,
        "title": "Exploratory Data Analysis (EDA) Master Summary",
        "dataset_uri": "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1",
        "total_records": 180519,
        "total_columns": 52,
        "overall_delay_rate_pct": 54.83,
        "steps": {}
    }
    for step_num in range(1, 8):
        json_file = os.path.join(REPORTS_DIR, f"step{step_num}_summary.json")
        if os.path.exists(json_file):
            with open(json_file, "r") as f:
                master["steps"][f"step_{step_num}"] = json.load(f)

    master_path = os.path.join(REPORTS_DIR, "eda_summary.json")
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2)
    print("Compiled master summary:", master_path)

if __name__ == "__main__":
    print("Generating Phase 3 Visualizations...")
    plot_delivery_status()
    plot_shipping_mode_delays()
    plot_market_performance()
    plot_monthly_order_trends()
    plot_sales_and_profit_trends()
    plot_category_distribution()
    plot_customer_segments()
    plot_correlation_heatmap()
    plot_regional_performance()
    plot_scheduled_vs_actual_days()
    plot_discount_vs_profitability()
    plot_payment_type_risk()
    compile_master_summary()
    print("All Step 8 visualizations and master summary successfully created!")

