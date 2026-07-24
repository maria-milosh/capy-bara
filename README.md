## Project Purpose

This project downloads population and geography data from the Census Bureau API and IPUMS/NHGIS, constructs adjacency graphs where census units (e.g. tracts) within study areas (e.g. CBSAs) are connected if they share a border, and applies a battery of residential segregation metrics. The goal is to assess segregation and disagreement among metrics across geographies and decades.

## Quick start

```bash
make install   # install Python dependencies via Poetry
make setup     # scaffold the data directory tree
make run       # run the baseline experiment
make run EXPERIMENT=h4_t3_observed_diffusion  # run a specific experiment
```

A Census API key and IPUMS API key are required for data downloads:

```bash
export CENSUS_API_KEY="..."
export IPUMS_API_KEY="..."
```

Install `parallel` to run the main pipeline: `brew install parallel` on Mac or `sudo apt-get install parallel` on Linux.

## Folder structure

```
capy-bara/
├── data/
│   ├── raw/                        # downloaded source files (gitignored)
│   ├── interim/                    # processed intermediates (gitignored)
│   └── outputs/                    # pipeline run outputs
│
├── pipeline/                       # core pipeline modules
│   ├── download/                   # download_geographies.py, download_population_tables.py
│   ├── preprocessing/              # census_geographies.py, study_areas.py, overlaps.py
│   ├── graphs.py                   # builds and contracts dual adjacency graphs
│   ├── metrics.py                  # computes segregation metrics
│   ├── process_results.py          # parses and aggregates metric outputs
│   ├── visualization/              # generate_figures.py and plot helpers
│   ├── utils/                      # definitions.py, visualization_settings.py
│   ├── config.yaml                 # pipeline configuration
│   └── tests/
│
├── experiments/                    # hypothesis-testing experiments
│   ├── notebooks/                  # scratch notebooks
│   ├── baseline/                   # default experiment config
│   ├── h<N>_t<N>_<name>/           # one folder per experiment
│   ├── experiment_orchestration.py
│   └── defaults.json
│
├── scripts/                        # shell scripts for running the pipeline
├── Makefile                        # common commands (install, setup, test, run)
```

## Pipeline overview

The full pipeline is driven by `scripts/reproduce.sh`, which sources `scripts/pipeline_config.sh` for all configuration. Steps run in order:

1. **`scripts/setup.sh`** — scaffolds the directory tree
2. **`pipeline/download/download_population_tables.py`** — downloads decennial census race/ethnicity counts (TOTPOP, WHITE, BLACK, POC, etc.) via Census API; uses IPUMS/NHGIS extracts for 1980 and 1990
3. **`pipeline/download/download_geographies.py`** — downloads TIGER/Line shapefiles (2000–2020 via Census API; 1980/1990 via IPUMS NHGIS)
4. **`pipeline/preprocessing/census_geographies.py`** — joins population tables to shapefiles, producing one attributed shapefile per year/level in `data/interim/census_geographies/`
5. **`pipeline/preprocessing/study_areas.py`** — builds study area boundary polygons (e.g. CBSA outlines from county-component `.xls` files) into `data/interim/study_areas/definitions/`
6. **`pipeline/preprocessing/overlaps.py`** — clips census geography shapefiles to each study area boundary (parallelized over years); outputs clipped shapefiles to `data/interim/study_areas/<year>/` and coverage stats to `data/outputs/<run>/coverage_stats.csv`
7. **`pipeline/graphs.py`** — builds the dual adjacency graph from each clipped shapefile; contracts zero-population nodes and ensures full connectivity; outputs `*_orig.json` and `*_connected.json` alongside each shapefile
8. **`pipeline/metrics.py`** — computes ~80 segregation metrics per study area / year from each connected graph JSON; outputs one CSV row per area; errors logged to `data/outputs/<run>/metric_failures.csv`
9. **`pipeline/visualization/generate_figures.py`** — reads aggregated metric CSVs and produces publication figures

`_orig.json` = raw dual graph; `_connected.json` = fully connected, zero-pop nodes contracted (used for metrics).

## Configuration

All pipeline behavior is controlled by environment variables (with defaults in `scripts/pipeline_config.sh`):

| Variable | Default | Options |
|---|---|---|
| `STUDY_AREA_TYPE` | `cbsa` | `cbsa`, `county` |
| `CENSUS_GEOGRAPHY_TYPE` | `tracts` | `tracts`, `block_groups`, `blocks`, `counties` |
| `CENSUS_GEOGRAPHY_YEARS` | `2020 2010 2000 1990 1980` | space-separated year list |
| `STUDY_AREA_VINTAGE` | `2020` | year |
| `RUN_NAME` | `<geo_type>_in_<study_area_type>` | string |
| `RUN_OUTPUT_DIR` | `data/outputs/<RUN_NAME>` | path |

For `STUDY_AREA_TYPE=cbsa`, a delineation file matching `list1_*_<vintage>.xls` must exist in `data/interim/study_area_sources/`.

## Dependencies

Python deps are managed via Poetry. See `pyproject.toml` for the full list.

```bash
pip install poetry
make install # equivalent to: poetry install
poetry shell # activate the Poetry environment
```
