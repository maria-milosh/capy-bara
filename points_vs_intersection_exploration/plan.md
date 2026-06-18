# Plan: Representative Points vs. Any Intersection

## Goal

Compare CBSA tract assignments created by the new representative-point method in
`cbsas/` against the old any-intersection method in `old_cbsas/`, focusing on
the March 2020 CBSA definition vintage for now. Quantify how assignment
differences affect tract counts, population totals, race composition, graph
structure, and segregation metrics.

This should extend the existing `points_vs_intersection_exploration/` audit
without rewriting heavy generated folders. The comparison should produce small
CSV summaries and figures only.

## Current Starting Point

Already available in `points_vs_intersection_exploration/`:

- `compare_outputs.py` compares which `.shp` outputs exist in `cbsas/` and
  `old_cbsas/`.
- `counts_by_year.csv` gives old/new/common/missing/new-only output counts by
  year.
- `missing_*` CSVs describe old intersection outputs that disappeared under the
  representative-point method.
- `diagnose_missing_contents.py` summarizes the contents of those old-only
  outputs.

Initial all-vintage file-count result: representative-point outputs are a
subset of the old intersection outputs for all checked years. The count
differences are visible in 1970 and 1980, while 1990 onward has the same number
of `.shp` outputs. The main analysis below should filter to the March 2020
vintage, and content differences may still exist inside matching outputs in
every year, so the next step must compare tract membership and population, not
just file presence.

## Unit of Comparison

Filter all comparison inputs to the March 2020 vintage. In practice, that means
using stems that end with `_march_2020`, such as
`9618502_16980_march_2020`.

Use `(year, stem)` as the primary key, where `stem` is the shapefile basename
with `_cbsa_tracts` removed. Because this phase is restricted to one vintage,
`(year, cbsa_code)` should usually be equivalent for reporting, but keeping the
stem in the tables makes filenames and graph paths unambiguous.

Also report unique metro counts by `(year, cbsa_code)` separately from physical
output counts. This keeps the current March 2020 analysis clean while still
making it possible to compare against the earlier all-vintage audit.

For each `(year, stem)`:

- `common`: exists in both `old_cbsas/` and `cbsas/`.
- `old_only`: exists only in `old_cbsas/`.
- `new_only`: exists only in `cbsas/`.

For content-level comparisons, compare paired `common` outputs directly and
summarize `old_only`/`new_only` as unmatched changes.

## Core Tables to Build

Add a script such as
`points_vs_intersection_exploration/compare_assignment_contents.py` that reads
the old and new shapefiles with `geopandas` and writes these CSVs:

1. `assignment_comparison_by_cbsa.csv`

   One row per `(year, stem)` with:

   - metadata: `year`, `stem`, `cbsa_code`, `cbsa_title`, `vintage`, `status`
   - paths: `old_path`, `new_path`
   - tract counts: `old_tract_count`, `new_tract_count`, `tract_count_delta`,
     `tract_count_pct_delta`
   - membership counts: `retained_tract_count`, `removed_tract_count`,
     `added_tract_count`
   - total population: `old_total_population`, `new_total_population`,
     `population_delta`, `population_pct_delta`
   - race totals and deltas for available columns: `WHITE`, `BLACK`, `AMIN`,
     `ASIAN`, `2MORE`, `POC`
   - graph counts from existing JSONs: `old_orig_nodes`, `new_orig_nodes`,
     `old_orig_edges`, `new_orig_edges`, `old_connected_nodes`,
     `new_connected_nodes`, `old_connected_edges`, `new_connected_edges`
   - graph deltas: node deltas, edge deltas, average-degree deltas, component
     count deltas in original graphs, and node contraction deltas from original
     to connected graphs

2. `tract_membership_changes.csv`

   One row per tract that was added or removed within a common CBSA/year:

   - `year`, `stem`, `cbsa_code`, `cbsa_title`, `vintage`
   - `change_type`: `removed_by_points` or `added_by_points`
   - tract identifier, preferably `GISJOIN`
   - population and race columns
   - available geography columns such as state, county, tract name, land/water
     area

3. `assignment_summary_by_year.csv`

   One row per year with:

   - old/new physical output counts
   - old/new unique CBSA counts
   - common/old-only/new-only counts
   - tract-count summary: mean, median, min, max for old and new
   - total-population summary: mean, median, min, max for old and new
   - aggregate added/removed/net population by race

4. `assignment_outliers.csv`

   Top changed metro areas by:

   - absolute tract-count delta
   - percent tract-count delta, with a minimum old tract-count threshold
   - absolute total-population delta
   - percent total-population delta, with a minimum old population threshold
   - race-specific absolute and percent deltas
   - graph-structure deltas, especially large node/edge changes and changes in
     original graph component counts

5. `graph_structure_comparison_by_cbsa.csv`

   One row per `(year, stem)` with graph-specific diagnostics from both
   `_orig.json` and `_connected.json`:

   - original graph: nodes, edges, connected component count, largest component
     share, isolated node count, average degree
   - connected graph: nodes, edges, connected component count, isolated node
     count, average degree
   - contraction summary: nodes removed from original to connected graph,
     edges changed from original to connected graph
   - old-vs-new deltas for each field
   - optional joins to existing `gen_duals_islands.csv` and
     `gen_duals_large_populated_overlaps.csv` to explain changes caused by
     islands or geometry overlaps

Use `GISJOIN` as the tract identity column. If a year ever lacks `GISJOIN`, add
a small fallback helper that checks common alternatives before failing with a
clear error.

## Comparisons and Figures

### 1. Metro Area Counts and Chicago Example

Reuse:

- `compare_outputs.py`
- `counts_by_year.csv`
- `missing_metro_areas_by_year.csv`
- `missing_cbsa_codes_by_year.csv`

Add:

- A grouped or stacked bar chart of old/new/common/old-only/new-only physical
  output counts by year, filtered to March 2020 outputs.
- A second count summary using unique `(year, cbsa_code)` so the narrative can
  distinguish metro areas from physical shapefile outputs.
- A Chicago side-by-side map. Use CBSA code `16980`, the `march_2020`
  definition, and one year such as 2020 for a clean example. Plot:
  - left: old any-intersection tracts
  - right: new representative-point tracts
  - same CRS, extent, line width, and color scale
  - optional inset or third difference figure marking retained, removed, and
    added tracts

Suggested output:

- `figures/points_vs_intersection/metro_counts_by_year.png`
- `figures/points_vs_intersection/chicago_16980_march_2020_2020_side_by_side.png`
- optional:
  `figures/points_vs_intersection/chicago_16980_march_2020_2020_difference.png`

### 2. Tract Count Distributions

For common outputs, compute old and new tract counts per metro area/year.
Include old-only outputs in a separate status panel or annotation so they do not
look like zero-tract new metros.

Figures:

- two histograms, one for old tract counts and one for new tract counts, using
  shared bins and axis limits
- optional faceting by year if the all-year distribution hides year-specific changes
- optional delta histogram for `new_tract_count - old_tract_count`

Statistics to report:

- average tract count
- median tract count
- min and max
- count of metros with no change, fewer tracts, and more tracts

### 3. Total Population Changes

For each common output, sum `TOTPOP` in both shapefiles and compute raw and
percent differences.

Figures:

- two histograms of total population, old vs new, on the same graph, slightly transparent so that both are visible (all years together)
- a delta distribution for `new_total_population - old_total_population`
- population count change and percentage change histograms side by side with a log-scaled x-axis
- optional scatterplot of old vs new total population with a `y = x` reference line, per each year separately, as tiles of the same picture

Statistics to report:

- average, median, min, and max total population for old and new
- total aggregate population removed/added/net by year
- largest absolute and percent population changes

For percent changes, use a minimum old population threshold for outlier labels so very small metros do not dominate the list.

### 4. Population Change by Race

Race columns available from preprocessing are expected to include `WHITE`,
`BLACK`, `AMIN`, `ASIAN`, `2MORE`, plus derived `POC`. Treat `POC` as a derived
summary, not as an additive race category in the same stacked total as the
individual race columns.

Comparisons:

- aggregate added population by race
- aggregate removed population by race
- aggregate net change by race
- per-CBSA race deltas and percent deltas

Figures:

- horizontal bar plot of aggregate net population change by race
- horizontal bar plot grouped by year, showing removed percentages split by race (so each bar shows a percentage of that racial group removed, and bars are grouped by year)
- top-outlier chart labeling metro areas with the largest race-specific jumps
- optional scatterplot of population delta vs race-share delta for major groups

Outlier strategy:

- rank by absolute race-population delta
- also rank by race percent delta where the old race population exceeds a
  minimum threshold
- report both, because large metros and small metros answer different questions

### 5. Graph Structure Changes

Compare graph structure for the March 2020 vintage using the existing
`_orig.json` and `_connected.json` files in both `old_cbsas/` and `cbsas/`.
This is useful because the metric pipeline does not operate directly on the raw
shapefiles; it operates on connected graphs after islands are connected and
zero-population nodes are contracted.

Comparisons:

- old vs new node counts in original graphs
- old vs new edge counts in original graphs
- old vs new connected component counts before graph repair
- old vs new isolated node counts before graph repair
- old vs new node and edge counts in connected graphs
- original-to-connected node contraction counts for each method
- changes in average degree or edge density

Figures:

- old-vs-new scatterplots for connected graph nodes and edges
- histograms of node and edge deltas
- bar chart of total original components or islands by year and method
- outlier plot for metro areas with the largest graph-structure jumps
- scatterplot of metric delta vs connected-node or connected-edge delta after
  the metrics are computed

Statistics to report:

- average, median, min, and max connected graph nodes and edges
- average original component count by year and method
- count of metro graphs where the representative-point method changes
  component count
- top metro areas by node, edge, and component-count changes

### 6. Segregation Metric Outcomes

Use `pipeline/calculate_metrics.py` on connected graph JSONs from both roots. Use poetry venv to access the packages needed for this.
The file is `pipeline/calculate_metrics.py` even if it is accidentally referred
to elsewhere as `calcualte_metrics.py`. Then apply `scripts/parse_output.py` to the outcomes to save csvs for line plots, and `scripts/generate_figures.py` to generate line plots for the old intersection method and the new points method.

Connected JSONs already exist for both `old_cbsas/` and `cbsas/`, reuse them.
Filter metric runs and comparisons to March 2020 connected graphs.

Recommended metric runs:

- `BLACK WHITE TOTPOP`
- `POC WHITE TOTPOP`

Suggested outputs:

- `points_vs_intersection_exploration/outputs/white_black_old_intersection.csv`
- `points_vs_intersection_exploration/outputs/white_black_points.csv`
- `points_vs_intersection_exploration/outputs/white_poc_old_intersection.csv`
- `points_vs_intersection_exploration/outputs/white_poc_points.csv`
- parsed comparison tables in `points_vs_intersection_exploration/`

Metric comparison table:

- join old and new parsed metric outputs by `(year, stem, x_col, y_col,
  tot_col)`
- compute `new_metric - old_metric` and percent/rank changes where meaningful
- include graph-level changes already emitted by `calculate_metrics.py`:
  `total_nodes`, `total_edges`, `total_population`, race totals
- join to `graph_structure_comparison_by_cbsa.csv` so metric changes can be
  interpreted alongside node, edge, and component changes

Figures:

- run 
- old-vs-new scatterplots with `y = x` lines for each metric
- delta histograms for key metrics
- heatmap of average absolute metric delta by year and metric
- metric delta vs tract-count delta
- metric delta vs population delta
- top changed metro areas table/plot for each metric family

## Notes

- Focus on March 2020 first. The existing all-vintage audit is still useful
  background, but the first content, graph, and metric comparisons should avoid
  vintage-to-vintage noise.
- Separate physical output counts from unique metro counts. Even within a
  single vintage, this keeps the terms precise and avoids carrying over
  assumptions from the all-vintage audit.
- Separate unmatched outputs from paired content changes. Old-only outputs in
  1970/1980 should be described, but paired old/new histograms should not treat
  them as zeros.
- Add tract membership deltas. Counts and totals say how much changed; added and
  removed tract lists say what changed.
- Use shared bins and axes in paired histograms. Otherwise old/new distribution
  plots can be visually misleading.
- Include percent changes with thresholds. Absolute changes identify major
  metros; percent changes identify places where the method meaningfully changes
  a smaller metro.
- Include graph structure as a first-class outcome. The metrics run on
  connected graph JSONs, so `total_nodes`, `total_edges`, components/islands,
  and zero-population contractions can explain metric changes that are not
  obvious from shapefile tract counts alone.
- Validate population conservation between shapefiles and connected graphs.
  Graph contraction should not change total population, but it can change node
  counts.
- Keep `POC` separate from race-category totals. It is useful for metric runs
  but overlaps with `BLACK`, `AMIN`, `ASIAN`, and `2MORE`.
- Add a short narrative for outliers. Big jumps should be mapped or inspected so
  the final writeup can distinguish expected boundary behavior from data or
  geometry issues.

## Implementation Order

1. Build `compare_assignment_contents.py` and generate the core CSVs listed
   above, filtered to March 2020 outputs.

2. Generate count, tract-count, population, race-change, graph-structure, and
   Chicago map figures from the comparison CSVs.

3. Run `pipeline/calculate_metrics.py` for the old and new connected JSONs,
   filtered to March 2020, parse outputs with `scripts/parse_output.py`, and
   build a joined metric comparison table.

4. Generate metric comparison figures and top-outlier summaries. *(This part is only partly done. Final line plots are created but nothing else because the line plots suggest no serious changes took place at least in the aggregated by year form.)*

5. Write a short results note in this folder summarizing:

   - where counts changed
   - how tract/population/race composition changed
   - how graph structure changed
   - which metro areas are outliers
   - whether segregation metrics are robust to the assignment method

## Verification Checks

- Confirm every common `(year, stem)` has both old and new shapefiles before
  computing paired deltas.
- Confirm race sums are numeric and missing columns are handled consistently by
  year.
- Confirm `TOTPOP` from shapefile rows matches `total_population` from the
  connected graph metric output for the same side.
- Spot-check Chicago and at least one high-delta outlier visually.
- Avoid running `bash reproduce.sh` for this comparison unless the full dataset
  truly needs to be regenerated.
