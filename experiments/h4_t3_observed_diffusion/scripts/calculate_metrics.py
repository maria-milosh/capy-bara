# Calculate metrics for one (for now manually selected) cluster-year area and save

import argparse
from pathlib import Path
import numpy as np
from os import mkdir
import gerrychain
import networkx as nx
import pandas as pd


selections = pd.read_csv('../data/candidate_tracts.csv')
graph_dir = Path("../../../data/processed/dual_graphs")


def calculate_cluster_metrics(
    graph, gisjoins, core_gisjoins):
    """
    Calculates metrics for one supplied cluster-year area and core cluster.
    Parameters:
    ----------
    graph: gerrychain.Graph
        The dual graph for the CBSA and year of interest.
    gisjoins: list of str
        The GISJOINs of the tracts in the catchment.
    core_gisjoins: list of str
        The GISJOINs of the tracts in the core.
    Returns
    -------
    dict
        A dictionary containing the calculated metrics for the catchment area and core cluster.
    """
    # Translate the supplied catchment area and core GISJOINs to graph node IDs, {GISJOIN: node_id}
    nodes_by_gisjoin = {str(attrs["GISJOIN"]): node for node, attrs in graph.nodes(data=True)}
    selected_nodes = [nodes_by_gisjoin[gisjoin] for gisjoin in gisjoins]
    core_nodes = [nodes_by_gisjoin[gisjoin] for gisjoin in core_gisjoins]

    # Sum the population contained in the supplied catchment area
    black_population = sum(int(graph.nodes[node]["BLACK"]) for node in core_nodes)
    # print(f"Black population in cluster area: {black_population}")
    total_population = sum(int(graph.nodes[node]["TOTPOP"]) for node in core_nodes)
    # print(f"Total population in cluster area: {total_population}")

    # Test every core tract and pick the graph centroid. Centroid minimizes the sum of distances to all other tracts in the catchment area, weighted by Black population.
    best_center = None
    best_objective = None
    for candidate in core_nodes:
        distances = nx.single_source_shortest_path_length(graph, candidate)
        objective = sum(
            int(graph.nodes[node]["BLACK"]) * distances[node] for node in core_nodes)
        # The candidate tract itself contributes zero because its distance to itself is zero
        # tie_break = str(graph.nodes[candidate]["GISJOIN"])
        if best_objective is None or objective < best_objective: # (objective, tie_break) < (best_objective, str(graph.nodes[best_center]["GISJOIN"])):
            best_center = candidate
            best_objective = objective

    selected_subgraph = graph.subgraph(core_nodes)
    return {
        "tract_count": len(core_nodes),
        "catchment_component_count": nx.number_connected_components(selected_subgraph), # should be 1
        "core_tract_count": len(core_nodes),
        "black_population": black_population,
        "total_population": total_population,
        "black_share": black_population / total_population,
        "spread_edges": best_objective / black_population,
        # "core_black_population": sum(
        #     int(graph.nodes[node]["BLACK"]) for node in core_nodes),
        "center_node_id": best_center,
        "center_gisjoin": graph.nodes[best_center]["GISJOIN"],
        "center_geoid": graph.nodes[best_center].get("GEOID")}


output_rows = []
for (cbsa, year, cluster), group in selections.groupby(["cbsa", "year", "cluster"], sort=True):
    print(f"Calculating metrics for CBSA {cbsa}, year {year}, cluster {cluster}.")
    # find and read the dual graph for this CBSA and year:
    matches = sorted(
            (graph_dir / str(year)).glob(
                f"tracts_in_cbsa_{cbsa}_{year}_*_connected.json"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one connected graph for CBSA {cbsa} in {year}, but found {len(matches)}.")
    graph = gerrychain.Graph.from_json(matches[0])

    # Determine which tracts in the catchment area are part of the core cluster
    is_core = group["is_core"].astype(str).str.lower().eq("true")
    # Threshold used to define the catchment area is the same for all tracts, so just take the 1st value
    catchment_threshold = group["catchment_threshold"].iloc[0]
    # Core tracts IDs:
    core_gisjoins = group.loc[is_core, "gisjoin"].tolist()

    metrics = calculate_cluster_metrics(graph, group["gisjoin"].tolist(), core_gisjoins)
    
    output_rows.append(
        {"cbsa": cbsa,
            "year": year,
            "cluster": cluster,
            "catchment_threshold": catchment_threshold, 
            # "selection_method": (group["selection_method"].iloc[0]),
            **metrics})


    mkdir("outputs") if not Path("outputs").exists() else None
    pd.DataFrame(output_rows).sort_values(["cbsa", "cluster", "year"]).to_csv(
        "../data/cluster_metrics.csv", index=False)
    print(f"Wrote {len(output_rows)} cluster-year rows to data/cluster_metrics.csv")