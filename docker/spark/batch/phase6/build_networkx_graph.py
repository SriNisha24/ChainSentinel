"""
ChainSentinel - Phase 6: Supply-Chain Graph Construction
Step 5 & 6: NetworkX Graph Construction, Analytics & Exports

Loads extracted node and edge datasets, constructs the heterogeneous directed
operational graph using NetworkX, computes network topology metrics, degree distributions,
connectivity, centrality indices, and operational concentration.
Exports GraphML, JSON, and comprehensive analytical summaries.

Execution:
    Host Python virtual environment with NetworkX 3.7
"""

import os
import sys
import json
import time
import logging
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase6_NetworkXGraph")

DATA_DIR = r"E:\BDA\ChainSentinel\data\phase6"
REPORTS_DIR = r"E:\BDA\ChainSentinel\reports\phase6"

NODES_CSV = os.path.join(DATA_DIR, "graph_nodes.csv")
EDGES_CSV = os.path.join(DATA_DIR, "graph_edges.csv")
BACKBONE_EDGES_CSV = os.path.join(DATA_DIR, "graph_backbone_edges.csv")

GRAPHML_OUT = os.path.join(DATA_DIR, "chainsentinel_graph.graphml")
JSON_OUT = os.path.join(DATA_DIR, "chainsentinel_graph.json")
SUMMARY_JSON_OUT = os.path.join(DATA_DIR, "graph_summary.json")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    start_time = time.time()
    logger.info("Loading graph nodes and edges from CSV...")

    df_nodes = pd.read_csv(NODES_CSV)
    df_edges = pd.read_csv(EDGES_CSV)
    df_backbone = pd.read_csv(BACKBONE_EDGES_CSV)

    logger.info(f"Loaded {len(df_nodes):,} nodes and {len(df_edges):,} edges.")

    # =========================================================================
    # 1. CONSTRUCT HETEROGENEOUS DIRECTED GRAPH
    # =========================================================================
    logger.info("Initializing NetworkX DiGraph...")
    G = nx.DiGraph(name="ChainSentinel_Heterogeneous_Operational_Graph")

    # Add Nodes with sanitized, typed attributes
    for _, row in df_nodes.iterrows():
        node_id = str(row["node_id"])
        attrs = {
            "node_type": str(row["node_type"]),
            "label": str(row["label"]) if pd.notna(row["label"]) else node_id,
            "order_count": int(row["order_count"]) if pd.notna(row["order_count"]) else 0,
            "total_spend": float(row["total_spend"]) if pd.notna(row["total_spend"]) else 0.0,
            "total_profit": float(row["total_profit"]) if pd.notna(row["total_profit"]) else 0.0,
            "delayed_orders": int(row["delayed_orders"]) if pd.notna(row["delayed_orders"]) else 0
        }
        G.add_node(node_id, **attrs)

    # Add Edges with attributes
    for _, row in df_edges.iterrows():
        src = str(row["source"])
        tgt = str(row["target"])
        attrs = {
            "relationship": str(row["relationship"]),
            "weight": float(row["weight"]) if pd.notna(row["weight"]) else 1.0,
            "volume": int(row["volume"]) if pd.notna(row["volume"]) else 1,
            "revenue": float(row["revenue"]) if pd.notna(row["revenue"]) else 0.0
        }
        G.add_edge(src, tgt, **attrs)

    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    logger.info(f"Constructed Graph: {num_nodes:,} nodes, {num_edges:,} edges.")

    # =========================================================================
    # 2. GRAPH TOPOLOGY & STRUCTURAL ANALYTICS
    # =========================================================================
    logger.info("Computing network metrics...")

    # Node count by type
    node_type_counts = df_nodes["node_type"].value_counts().to_dict()
    # Edge count by relationship
    edge_rel_counts = df_edges["relationship"].value_counts().to_dict()

    # Degree statistics
    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())
    total_degrees = dict(G.degree())

    deg_vals = list(total_degrees.values())
    max_deg = max(deg_vals)
    avg_deg = float(np.mean(deg_vals))
    median_deg = float(np.median(deg_vals))

    # Weakly connected components
    weakly_connected = list(nx.weakly_connected_components(G))
    num_weakly_connected = len(weakly_connected)
    largest_wcc_size = max(len(c) for c in weakly_connected)

    logger.info(f"Weakly connected components: {num_weakly_connected}, Largest WCC size: {largest_wcc_size:,}")

    # Top Centrality Nodes across the Network
    logger.info("Computing degree centrality...")
    degree_centrality = nx.degree_centrality(G)
    top_degree_centrality = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:20]

    top_deg_list = []
    for nid, cent in top_degree_centrality:
        top_deg_list.append({
            "node_id": nid,
            "node_type": G.nodes[nid].get("node_type", "Unknown"),
            "label": G.nodes[nid].get("label", nid),
            "degree": total_degrees[nid],
            "in_degree": in_degrees[nid],
            "out_degree": out_degrees[nid],
            "degree_centrality": round(cent, 6)
        })

    # =========================================================================
    # 3. OPERATIONAL BACKBONE SUBGRAPH (CENTRALITY & VISUALIZATION CORE)
    # =========================================================================
    logger.info("Constructing Operational Backbone Subgraph...")
    # Backbone nodes: Products, Categories, Departments, Regions, Markets, Shipping Modes
    backbone_node_types = {"Product", "Category", "Department", "Region", "Market", "Shipping_Mode"}
    backbone_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") in backbone_node_types]
    
    # Create Backbone Graph with aggregated flows
    G_backbone = nx.DiGraph(name="ChainSentinel_Operational_Backbone")
    for bn in backbone_nodes:
        G_backbone.add_node(bn, **G.nodes[bn])
    
    for _, row in df_backbone.iterrows():
        s = str(row["source"])
        t = str(row["target"])
        if s in G_backbone and t in G_backbone:
            G_backbone.add_edge(s, t,
                                relationship=str(row["relationship"]),
                                weight=float(row["weight"]),
                                volume=int(row["volume"]),
                                revenue=float(row["revenue"]))

    bb_nodes_count = G_backbone.number_of_nodes()
    bb_edges_count = G_backbone.number_of_edges()
    logger.info(f"Backbone Subgraph: {bb_nodes_count} nodes, {bb_edges_count} edges.")

    # Betweenness Centrality on Backbone Graph
    logger.info("Computing exact betweenness centrality on Backbone Subgraph...")
    bb_betweenness = nx.betweenness_centrality(G_backbone, weight=None)
    top_betweenness = sorted(bb_betweenness.items(), key=lambda x: x[1], reverse=True)[:15]

    top_btw_list = []
    for nid, btw in top_betweenness:
        top_btw_list.append({
            "node_id": nid,
            "node_type": G_backbone.nodes[nid].get("node_type", "Unknown"),
            "label": G_backbone.nodes[nid].get("label", nid),
            "betweenness_centrality": round(btw, 6)
        })

    # =========================================================================
    # 4. OPERATIONAL CONCENTRATION ANALYTICS
    # =========================================================================
    logger.info("Computing operational concentration...")

    # Product Concentration
    prod_nodes = df_nodes[df_nodes["node_type"] == "Product"].sort_values("total_spend", ascending=False)
    total_prod_rev = prod_nodes["total_spend"].sum()
    top_5_prod_rev = prod_nodes.head(5)["total_spend"].sum()
    top_10_prod_rev = prod_nodes.head(10)["total_spend"].sum()

    top_5_prod_pct = round(top_5_prod_rev / total_prod_rev * 100.0, 2)
    top_10_prod_pct = round(top_10_prod_rev / total_prod_rev * 100.0, 2)

    # Regional Concentration
    reg_nodes = df_nodes[df_nodes["node_type"] == "Region"].sort_values("total_spend", ascending=False)
    total_reg_rev = reg_nodes["total_spend"].sum()
    top_3_reg_rev = reg_nodes.head(3)["total_spend"].sum()
    top_3_reg_pct = round(top_3_reg_rev / total_reg_rev * 100.0, 2)

    # Customer Order Frequency Concentration
    cust_nodes = df_nodes[df_nodes["node_type"] == "Customer"]
    max_cust_orders = int(cust_nodes["order_count"].max())
    mean_cust_orders = round(float(cust_nodes["order_count"].mean()), 2)
    single_order_custs = int((cust_nodes["order_count"] == 1).sum())
    repeat_custs = len(cust_nodes) - single_order_custs

    concentration_summary = {
        "product_revenue_concentration": {
            "total_products": len(prod_nodes),
            "top_5_products_revenue_pct": top_5_prod_pct,
            "top_10_products_revenue_pct": top_10_prod_pct,
            "top_product": {
                "name": str(prod_nodes.iloc[0]["label"]),
                "revenue": float(prod_nodes.iloc[0]["total_spend"]),
                "order_count": int(prod_nodes.iloc[0]["order_count"])
            }
        },
        "regional_revenue_concentration": {
            "total_regions": len(reg_nodes),
            "top_3_regions_revenue_pct": top_3_reg_pct,
            "top_region": {
                "name": str(reg_nodes.iloc[0]["label"]),
                "revenue": float(reg_nodes.iloc[0]["total_spend"]),
                "order_count": int(reg_nodes.iloc[0]["order_count"])
            }
        },
        "customer_behavior": {
            "total_customers": len(cust_nodes),
            "mean_orders_per_customer": mean_cust_orders,
            "max_orders_by_single_customer": max_cust_orders,
            "single_order_customers": single_order_custs,
            "repeat_customers": repeat_custs,
            "repeat_customer_rate_pct": round(repeat_custs / len(cust_nodes) * 100.0, 2)
        }
    }

    # =========================================================================
    # 5. GRAPH EXPORTS (GraphML, JSON, and Summary JSON)
    # =========================================================================
    logger.info("Exporting graph artifacts...")

    # A. Export GraphML (Backbone Subgraph for interoperability and Gephi/Cytoscape visualization)
    logger.info(f"Saving Backbone GraphML to: {GRAPHML_OUT}")
    nx.write_graphml(G_backbone, GRAPHML_OUT)

    # B. Export JSON Format (Node-Link Structure for Web & Shockwave Engine ingestion)
    logger.info(f"Saving Backbone JSON to: {JSON_OUT}")
    json_data = nx.node_link_data(G_backbone)
    with open(JSON_OUT, "w") as f:
        json.dump(json_data, f, indent=2)

    # C. Export Comprehensive Graph Summary JSON
    logger.info(f"Saving Graph Summary JSON to: {SUMMARY_JSON_OUT}")
    graph_summary = {
        "graph_name": G.name,
        "directed": G.is_directed(),
        "total_nodes": num_nodes,
        "total_edges": num_edges,
        "node_type_distribution": node_type_counts,
        "edge_relationship_distribution": edge_rel_counts,
        "topology_metrics": {
            "max_degree": max_deg,
            "average_degree": round(avg_deg, 3),
            "median_degree": median_deg,
            "weakly_connected_components": num_weakly_connected,
            "largest_weakly_connected_component_nodes": largest_wcc_size,
            "is_weakly_connected": num_weakly_connected == 1
        },
        "top_degree_centrality_nodes": top_deg_list,
        "backbone_graph_metrics": {
            "backbone_nodes": bb_nodes_count,
            "backbone_edges": bb_edges_count,
            "top_betweenness_centrality_nodes": top_btw_list
        },
        "operational_concentration": concentration_summary,
        "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    with open(SUMMARY_JSON_OUT, "w") as f:
        json.dump(graph_summary, f, indent=2)

    logger.info(f"Graph construction completed in {time.time() - start_time:.2f} seconds.")

    # =========================================================================
    # 6. GENERATE PUBLICATION-QUALITY VISUALIZATIONS
    # =========================================================================
    logger.info("Generating publication-quality charts...")
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "axes.edgecolor": "#cccccc",
        "axes.linewidth": 0.8
    })

    # Visualization 1: Node-Type Distribution
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    types = list(node_type_counts.keys())
    counts = list(node_type_counts.values())
    colors = ["#2b5c8f", "#3498db", "#e67e22", "#2ecc71", "#e74c3c", "#9b59b6", "#1abc9c", "#f39c12", "#34495e"]
    bars = ax.bar(types, counts, color=colors[:len(types)], edgecolor="black", alpha=0.9, width=0.55)
    ax.set_yscale("log")
    ax.set_title("ChainSentinel Phase 6: Node Distribution by Entity Type (N = 86,780)", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Node Count (Log Scale)", fontsize=11)
    ax.tick_params(axis="x", labelrotation=25)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, h * 1.15, f"{int(h):,}", ha="center", va="bottom", fontsize=8, fontweight="bold")
    plt.tight_layout()
    v1_path = os.path.join(REPORTS_DIR, "phase6_node_distribution.png")
    plt.savefig(v1_path)
    plt.close()

    # Visualization 2: Edge-Type Distribution
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    rels = list(edge_rel_counts.keys())
    edge_counts = list(edge_rel_counts.values())
    bars = ax.barh(rels, edge_counts, color="#2980b9", edgecolor="black", alpha=0.85, height=0.55)
    ax.set_title("ChainSentinel Phase 6: Edge Distribution by Relationship Type (M = 357,211)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Observed Edge Count", fontsize=11)
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 2000, bar.get_y() + bar.get_height()/2.0, f"{int(w):,}", ha="left", va="center", fontsize=8, fontweight="bold")
    ax.set_xlim(0, max(edge_counts) * 1.15)
    plt.tight_layout()
    v2_path = os.path.join(REPORTS_DIR, "phase6_edge_distribution.png")
    plt.savefig(v2_path)
    plt.close()

    # Visualization 3: Operational Concentration (Pareto of Products & Regions)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=150)
    top_prod = prod_nodes.head(8)
    ax1.barh(top_prod["label"].str[:22], top_prod["total_spend"] / 1e6, color="#e67e22", edgecolor="black", alpha=0.85)
    ax1.set_title("Top 8 Products by Revenue ($M)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Revenue ($ Millions)", fontsize=10)
    ax1.invert_yaxis()

    top_reg = reg_nodes.head(8)
    ax2.barh(top_reg["label"].str[:22], top_reg["total_spend"] / 1e6, color="#27ae60", edgecolor="black", alpha=0.85)
    ax2.set_title("Top 8 Destination Regions by Revenue ($M)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Revenue ($ Millions)", fontsize=10)
    ax2.invert_yaxis()
    plt.tight_layout()
    v3_path = os.path.join(REPORTS_DIR, "phase6_operational_concentration.png")
    plt.savefig(v3_path)
    plt.close()

    # Visualization 4: Betweenness Centrality on Operational Backbone
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    btw_labels = [f"{x['label'][:20]} ({x['node_type']})" for x in top_btw_list[:10]]
    btw_scores = [x["betweenness_centrality"] for x in top_btw_list[:10]]
    bars = ax.barh(btw_labels, btw_scores, color="#8e44ad", edgecolor="black", alpha=0.85, height=0.55)
    ax.set_title("Top Operational Hubs by Betweenness Centrality (Backbone Network)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Betweenness Centrality Index", fontsize=11)
    ax.invert_yaxis()
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.005, bar.get_y() + bar.get_height()/2.0, f"{w:.4f}", ha="left", va="center", fontsize=8, fontweight="bold")
    ax.set_xlim(0, max(btw_scores) * 1.2)
    plt.tight_layout()
    v4_path = os.path.join(REPORTS_DIR, "phase6_centrality_analysis.png")
    plt.savefig(v4_path)
    plt.close()

    # Visualization 5: Operational Backbone Subgraph Network Layout
    fig, ax = plt.subplots(figsize=(11, 8), dpi=150)
    # Filter high-degree backbone nodes for clear visualization layout
    sample_nodes = [n for n in G_backbone.nodes() if G_backbone.degree(n) >= 15 or G_backbone.nodes[n].get("node_type") in {"Market", "Shipping_Mode", "Department"}]
    subG = G_backbone.subgraph(sample_nodes)
    
    pos = nx.spring_layout(subG, k=0.35, iterations=40, seed=42)
    
    node_colors_map = {
        "Market": "#e74c3c",
        "Region": "#f39c12",
        "Department": "#3498db",
        "Category": "#2ecc71",
        "Product": "#95a5a6",
        "Shipping_Mode": "#9b59b6"
    }
    node_c = [node_colors_map.get(subG.nodes[n].get("node_type", ""), "#cccccc") for n in subG.nodes()]
    node_s = [800 if subG.nodes[n].get("node_type") in {"Market", "Shipping_Mode", "Department"} else 250 for n in subG.nodes()]

    nx.draw_networkx_nodes(subG, pos, node_color=node_c, node_size=node_s, alpha=0.85, edgecolors="black", linewidths=0.8, ax=ax)
    nx.draw_networkx_edges(subG, pos, edge_color="#bdc3c7", width=0.7, alpha=0.6, arrows=True, arrowsize=8, ax=ax)
    
    # Label high-level nodes
    labels = {n: subG.nodes[n].get("label", n)[:14] for n in subG.nodes() if subG.nodes[n].get("node_type") in {"Market", "Department", "Shipping_Mode", "Region"}}
    nx.draw_networkx_labels(subG, pos, labels=labels, font_size=7, font_weight="bold", font_color="#2c3e50", ax=ax)

    # Custom Legend
    markers = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=col, markersize=10, label=nt) for nt, col in node_colors_map.items()]
    ax.legend(handles=markers, loc="upper right", frameon=True, fontsize=8)
    ax.set_title("ChainSentinel Operational Backbone Network (Macro Topology Flow)", fontsize=13, fontweight="bold", pad=12)
    ax.axis("off")
    plt.tight_layout()
    v5_path = os.path.join(REPORTS_DIR, "phase6_operational_graph.png")
    plt.savefig(v5_path)
    plt.close()

    print("All visualizations and graph exports completed successfully.")

if __name__ == "__main__":
    main()

