import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
import networkx as nx
import numpy as np
import os
from pathlib import Path
import gerrychain


# Read the saved catchment areas and centroids for Chicago; can be changed to Philly (CBSA 37980)
CBSA_selections = pd.read_csv('../data/candidate_tracts.csv', dtype={'cbsa': str, 'gisjoin': str})
CBSA_metrics = pd.read_csv( '../data/cluster_metrics.csv', dtype={'cbsa': str, 'center_gisjoin': str})
CBSA_selections = CBSA_selections[CBSA_selections['cbsa'] == '16980']
# CBSA_core = CBSA_selections[CBSA_selections['is_core'] == True]
CBSA_metrics = CBSA_metrics[CBSA_metrics['cbsa'] == '16980']
years = sorted(CBSA_metrics['year'].unique())
colors = {'hyde_park': "#b82ca5", 'austin': "#d69169"}


# Draw each selected catchment graph
fig, axes = plt.subplots(1, len(years), figsize=(20, 7))
for ax, year in zip(axes, years):
    graph_path = next(
        (Path('../../../data/processed/dual_graphs') / str(year)).glob(
            f'tracts_in_cbsa_16980_{year}_*_connected.json'))
    graph = gerrychain.Graph.from_json(graph_path)
    nodes_by_gisjoin = {
        str(attrs['GISJOIN']): node for node, attrs in graph.nodes(data=True)}
    # places each tract node at its real geographic centroid, so the graph resembles Chicago’s geography:
    positions = {
        node: (float(attrs['centroid_x']), float(attrs['centroid_y']))
        for node, attrs in graph.nodes(data=True)}

    max_black_count = CBSA_selections["black_population"].max()
    max_log_black = np.log1p(max_black_count)

    year_selections = CBSA_selections[CBSA_selections['year'] == year]
    for cluster, group in year_selections.groupby('cluster'):
        # print(cluster, group)
        area_nodes = [nodes_by_gisjoin[value] for value in group['gisjoin']]
        area_graph = graph.subgraph(area_nodes)
        area_black_count = group["black_population"].astype(float).to_numpy()
        # black_shares = group["black_share"].astype(float).to_numpy()
        # log_black_counts = np.log1p(group["cluster_black_population"].astype(float).to_numpy())

        nx.draw_networkx_edges(area_graph, positions, ax=ax, edge_color="black",
            width=0.5, alpha=0.45)
        nx.draw_networkx_nodes(area_graph, positions, ax=ax, nodelist=area_nodes,
            node_color=area_black_count, cmap="Blues", vmin=0, vmax=max_black_count, node_size=3)

        centroid_gisjoin = CBSA_metrics.loc[
            (CBSA_metrics['year'] == year) & (CBSA_metrics['cluster'] == cluster),
            'center_gisjoin'].iloc[0]
        centroid_tract = CBSA_selections.loc[
            (CBSA_selections['year'] == year) &
            (CBSA_selections['cluster'] == cluster) &
            (CBSA_selections['gisjoin'] == centroid_gisjoin)]
        centroid_black_population = centroid_tract['black_population'].iloc[0]
        centroid_black_share = centroid_tract['black_share'].iloc[0]

        centroid_x, centroid_y = positions[nodes_by_gisjoin[centroid_gisjoin]]
        ax.scatter(centroid_x, centroid_y, marker='*', s=120, color=colors[cluster],
            edgecolor='black', linewidth=0.5, zorder=3)
        if cluster == 'hyde_park':
            ax.annotate(f"Centroid's Black population:\n {cluster}: {centroid_black_population} ({centroid_black_share:.1%})",
                    xy=(1, 0), xycoords='axes fraction',
                    ha='right', va='top', fontsize=10, color='black')
        else:
            ax.annotate(f"\n\n{cluster}: {centroid_black_population} ({centroid_black_share:.1%})",
                        xy=(1, 0), xycoords='axes fraction',
                        ha='right', va='top', fontsize=10, color='black')

    ax.set_title(str(year))
    ax.set_aspect('equal')
    ax.axis('off')

# Add one shared legend and save the five-year figure
legend_items = [
    # Line2D([0], [0], color=colors['hyde_park'], marker='o', linestyle='-', label='Hyde Park'),
    # Line2D([0], [0], color=colors['austin'], marker='o', linestyle='-', label='Austin'),
    Line2D([0], [0], color='black', marker='*', markersize=13, linestyle='None', label='Selected centroid')]
fig.legend(handles=legend_items, loc='lower center', ncol=3)
fig.suptitle('Chicago cluster graphs and Black-population-weighted centroids')
fig.tight_layout(rect=(0, 0.08, 1, 0.94))
color_scale = plt.cm.ScalarMappable(
    norm=plt.Normalize(vmin=0, vmax= max_black_count),# max_log_black), #vmax=1),
    cmap="Blues")
# color_scale.set_array([])

fig.colorbar(color_scale, ax=axes, label="Black population", #"Log(Black population count + 1)",
    fraction=0.025, pad=0.02)
Path('../figures').mkdir(exist_ok=True)
figure_path = Path('../figures/chicago_cluster_centroids_all_years.png')
fig.savefig(figure_path, dpi=200, bbox_inches='tight')
plt.show()