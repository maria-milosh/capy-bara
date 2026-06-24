#!/usr/bin/env bash

set -euxo pipefail

. scripts/pipeline_config.sh

# Download NHGIS data

# Set up folder structure
bash scripts/setup.sh
mkdir -p "${RUN_OUTPUT_DIR}"
# SWAP_OUTPUT_DIR="${RUN_OUTPUT_DIR}/new_york_swaps/"

RUN_STARTED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
export METRIC_FAILURES_FILE="${RUN_OUTPUT_DIR}/metric_failures.csv"
{
    echo "start_timestamp=${RUN_STARTED_AT}"
    echo "run_name=${RUN_NAME}"
    echo "run_output_dir=${RUN_OUTPUT_DIR}"
    echo ""
    echo "graph_area_type=${STUDY_AREA_TYPE}"
    echo "nodes_area_type=${CENSUS_GEOGRAPHY_TYPE}"
    echo ""
    echo "study_area_vintage=${STUDY_AREA_VINTAGE}"
    echo "study_area_definition_vintage=${STUDY_AREA_DEFINITION_VINTAGE}"
    echo "study_area_source_file=${STUDY_AREA_SOURCE_FILE}"
    # echo "study_area_source_pattern=${STUDY_AREA_SOURCE_PATTERN}"
    echo "study_area_definition_geographies=${STUDY_AREA_DEFINITION_GEOGRAPHIES}"
    echo "study_area_definition_glob=study_areas/definitions/${STUDY_AREA_TYPE}_*_${STUDY_AREA_DEFINITION_VINTAGE}.shp"
    echo ""
    echo "census_geography_years=${CENSUS_GEOGRAPHY_YEARS}"
    # echo "census_geography_years_tag=${CENSUS_GEOGRAPHY_YEARS_TAG}"
    echo "reference_census_geography_year=${REFERENCE_CENSUS_GEOGRAPHY_YEAR}"
    echo "reference_study_area=${REFERENCE_STUDY_AREA}"
    echo "reference_overlap=${REFERENCE_OVERLAP}"
    echo ""
    # echo "swap_output_dir=${SWAP_OUTPUT_DIR}"
    # echo "swap_study_area=${SWAP_STUDY_AREA}"
    # echo "swap_census_geography_year=${SWAP_CENSUS_GEOGRAPHY_YEAR}"
} > "${RUN_LOG_FILE}"

# Build census geography shapefiles with population values
if [ "${CENSUS_GEOGRAPHY_TYPE}" = "tracts" ]; then
    python pipeline/build_census_geographies.py --years "${CENSUS_GEOGRAPHY_YEARS}"
fi

# Generate study area definition shapefiles from source file
bash scripts/build_study_areas.sh

# Select census geographies that overlap with study area definition shapefiles
bash scripts/overlaps.sh

# Generate dual graphs
# for year in ${CENSUS_GEOGRAPHY_YEARS}; do
#     fd "${CENSUS_GEOGRAPHY_TYPE}_in_${STUDY_AREA_TYPE}_.+_${year}_${STUDY_AREA_DEFINITION_VINTAGE}_vintage.shp" "study_areas/${year}"
# done | parallel --bar python pipeline/gen_duals.py {} {.}_orig.json {.}_connected.json
for year in ${CENSUS_GEOGRAPHY_YEARS}; do
    find "study_areas/${year}" \
        -type f \
        -name "${CENSUS_GEOGRAPHY_TYPE}_in_${STUDY_AREA_TYPE}_*_${year}_${STUDY_AREA_DEFINITION_VINTAGE}_vintage.shp"
done |
    parallel --bar python pipeline/gen_duals.py {} {.}_orig.json {.}_connected.json

# Calculate metrics, but first generate headers
python pipeline/calculate_metrics.py "study_areas/${REFERENCE_CENSUS_GEOGRAPHY_YEAR}/${REFERENCE_OVERLAP}_connected.json" BLACK WHITE TOTPOP --headers-only > "${RUN_OUTPUT_DIR}/white_black.csv"
for year in ${CENSUS_GEOGRAPHY_YEARS}; do
    fd "${CENSUS_GEOGRAPHY_TYPE}_in_${STUDY_AREA_TYPE}_.+_${year}_${STUDY_AREA_DEFINITION_VINTAGE}_vintage_connected.json" "study_areas/${year}" | parallel --bar python pipeline/calculate_metrics.py {} BLACK WHITE TOTPOP >> "${RUN_OUTPUT_DIR}/white_black.csv"
done

python pipeline/calculate_metrics.py "study_areas/${REFERENCE_CENSUS_GEOGRAPHY_YEAR}/${REFERENCE_OVERLAP}_connected.json" POC WHITE TOTPOP --headers-only > "${RUN_OUTPUT_DIR}/white_poc.csv"
for year in ${CENSUS_GEOGRAPHY_YEARS}; do
    fd "${CENSUS_GEOGRAPHY_TYPE}_in_${STUDY_AREA_TYPE}_.+_${year}_${STUDY_AREA_DEFINITION_VINTAGE}_vintage_connected.json" "study_areas/${year}" | parallel --bar python pipeline/calculate_metrics.py {} POC WHITE TOTPOP >> "${RUN_OUTPUT_DIR}/white_poc.csv"
done

# # New York swaps
# # python pipeline/random_swaps.py "study_areas/${SWAP_CENSUS_GEOGRAPHY_YEAR}/${SWAP_OVERLAP}_connected.json" "${SWAP_OUTPUT_DIR}"

# # python pipeline/calculate_metrics.py "study_areas/${REFERENCE_CENSUS_GEOGRAPHY_YEAR}/${REFERENCE_OVERLAP}_connected.json" BLACK WHITE TOTPOP --headers-only > "${RUN_OUTPUT_DIR}/new_york_swaps_white_black.csv"
# # fd json "${SWAP_OUTPUT_DIR}" | parallel --bar python pipeline/calculate_metrics.py {} BLACK WHITE TOTPOP >> "${RUN_OUTPUT_DIR}/new_york_swaps_white_black.csv"

# # python pipeline/calculate_metrics.py "study_areas/${REFERENCE_CENSUS_GEOGRAPHY_YEAR}/${REFERENCE_OVERLAP}_connected.json" BLACK WHITE TOTPOP --headers-only > "${RUN_OUTPUT_DIR}/new_york_swaps_white_poc.csv"
# # fd json "${SWAP_OUTPUT_DIR}" | parallel --bar python pipeline/calculate_metrics.py {} POC WHITE TOTPOP >> "${RUN_OUTPUT_DIR}/new_york_swaps_white_poc.csv"

# Generate figures
python pipeline/generate_figures.py --filename "${RUN_OUTPUT_DIR}/white_poc.csv" --prefix "white_poc_${OUTPUT_SUFFIX}"
python pipeline/generate_figures.py --filename "${RUN_OUTPUT_DIR}/white_black.csv" --prefix "white_black_${OUTPUT_SUFFIX}"
