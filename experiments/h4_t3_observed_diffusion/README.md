# H4 T3: Observed diffusion

This experiment measures changes in the mass and spread of four Black
population clusters:

- Chicago CBSA (`16980`): Hyde Park and Austin
- Philadelphia CBSA (`37980`): west of Germantown Avenue and West Philadelphia - need to confirm is these are the clusters we need

It uses the existing tract network in `data/rpocessed/dual_graphs/YEAR/*_connected.json` graphs for 1980, 1990, 2000, 2010, and 2020. Network distance is unweighted shortest-path length, measured in tract-adjacency edges.

## Current area of search definition

They are manual for now. Cluster and core tracts are taken from `data/candidate_tracts.csv` as supplied.

## Metrics

### Cluster center
For a search area A, Black population \(B_i\), and graph distance \(d(i,j)\) (n of edges between i and j): we go over all nodes j in the core cluster and find the j with minimum distance * Black population. This j is the centroid:

$$
c = \operatorname*{arg\,min}_{j \in A}
\sum_{i \in A} B_i d(i,j)
$$

The center is recalculated independently in every decade.

### Mass

Mass is just the $\sum(B_i)$.

### Spread

Spread is the mean distance from the center over all $B_i$:

$$
\frac{\sum_i B_i d(i,c)}{\sum_i B_i}
$$

Membership connectivity is evaluated from actual shared tract
borders in the GeoPackage, while distances use the connected JSON graph.
