# Set the variables below to configure the pipeline for a given run. You can set them in the environment before running this script, or you can edit this file directly. If you set them in the environment, they will override the values in this file.

# Variables: 
# STUDY_AREA_TYPE: The type of study area to analyze. Default is "cbsa". Possible values: "cbsa", "largest_county" (not implemented yet), "state" (not implemented yet).
# CENSUS_GEOGRAPHY_TYPE: A smaller geography to match to the study area. In other words, these are graph nodes. Default is "tracts". Possible values: "tracts", "block_groups" (not implemented yet), "blocks" (not implemented yet).
# CENSUS_GEOGRAPHY_YEARS: The years of census geography to analyze. Default is "2020 2010 2000 1990 1980".
# STUDY_AREA_VINTAGE: The vintage year of the study area definitions to use. Default is 2020. Possible values: 2020, 2010, 2000, 1990, 1980.

# To manually clean variables, run:
# `unset CENSUS_GEOGRAPHY_YEARS STUDY_AREA_VINTAGE`


STUDY_AREA_TYPE="${STUDY_AREA_TYPE:-cbsa}"
CENSUS_GEOGRAPHY_TYPE="${CENSUS_GEOGRAPHY_TYPE:-tracts}"
CENSUS_GEOGRAPHY_YEARS="${CENSUS_GEOGRAPHY_YEARS:-2020 2010 2000 1990 1980}"
STUDY_AREA_VINTAGE="${STUDY_AREA_VINTAGE:-2020}"


if [ -z "${STUDY_AREA_SOURCE_PATTERN:-}" ]; then
    if [ "${STUDY_AREA_TYPE}" = "cbsa" ]; then
        STUDY_AREA_SOURCE_PATTERN="list1_*_${STUDY_AREA_VINTAGE}.xls"
    else
        STUDY_AREA_SOURCE_PATTERN="${STUDY_AREA_TYPE}_*_${STUDY_AREA_VINTAGE}.*"
    fi
fi

if [ -z "${STUDY_AREA_SOURCE_FILE:-}" ]; then
    STUDY_AREA_SOURCE_FILE="$(find study_area_sources -maxdepth 1 -name "${STUDY_AREA_SOURCE_PATTERN}" | sort | tail -n 1)"
fi

if [ -z "${STUDY_AREA_SOURCE_FILE}" ]; then
    echo "No study area source file found for STUDY_AREA_TYPE=${STUDY_AREA_TYPE}, STUDY_AREA_VINTAGE=${STUDY_AREA_VINTAGE}, STUDY_AREA_SOURCE_PATTERN=${STUDY_AREA_SOURCE_PATTERN}" >&2
    exit 1
fi

STUDY_AREA_SOURCE_BASENAME="$(basename "${STUDY_AREA_SOURCE_FILE}")"
STUDY_AREA_SOURCE_STEM="${STUDY_AREA_SOURCE_BASENAME%.*}"

if [ -z "${STUDY_AREA_DEFINITION_VINTAGE:-}" ]; then
    if [ "${STUDY_AREA_TYPE}" = "cbsa" ] && [ "${STUDY_AREA_SOURCE_STEM#list1_}" != "${STUDY_AREA_SOURCE_STEM}" ]; then
        STUDY_AREA_DEFINITION_VINTAGE="${STUDY_AREA_SOURCE_STEM#list1_}"
    elif [ "${STUDY_AREA_SOURCE_STEM#${STUDY_AREA_TYPE}_}" != "${STUDY_AREA_SOURCE_STEM}" ]; then
        STUDY_AREA_DEFINITION_VINTAGE="${STUDY_AREA_SOURCE_STEM#${STUDY_AREA_TYPE}_}"
    else
        STUDY_AREA_DEFINITION_VINTAGE="${STUDY_AREA_SOURCE_STEM}"
    fi
fi

if [ -z "${STUDY_AREA_DEFINITION_GEOGRAPHIES:-}" ]; then
    if [ "${STUDY_AREA_VINTAGE}" = "2020" ]; then
        STUDY_AREA_DEFINITION_GEOGRAPHIES="census_geographies/2020_${CENSUS_GEOGRAPHY_TYPE}.shp"
    else
        STUDY_AREA_DEFINITION_GEOGRAPHIES="census_geographies/2010_${CENSUS_GEOGRAPHY_TYPE}.shp"
    fi
fi

FIRST_CENSUS_GEOGRAPHY_YEAR=""
for year in ${CENSUS_GEOGRAPHY_YEARS}; do
    if [ -z "${FIRST_CENSUS_GEOGRAPHY_YEAR}" ]; then
        FIRST_CENSUS_GEOGRAPHY_YEAR="${year}"
    fi
done
REFERENCE_CENSUS_GEOGRAPHY_YEAR="${REFERENCE_CENSUS_GEOGRAPHY_YEAR:-${FIRST_CENSUS_GEOGRAPHY_YEAR}}"
SWAP_CENSUS_GEOGRAPHY_YEAR="${SWAP_CENSUS_GEOGRAPHY_YEAR:-${REFERENCE_CENSUS_GEOGRAPHY_YEAR}}"

REFERENCE_STUDY_AREA_CODE="${REFERENCE_STUDY_AREA_CODE:-39460}"
SWAP_STUDY_AREA_CODE="${SWAP_STUDY_AREA_CODE:-35620}"
REFERENCE_STUDY_AREA="${STUDY_AREA_TYPE}_${REFERENCE_STUDY_AREA_CODE}_${STUDY_AREA_DEFINITION_VINTAGE}"
SWAP_STUDY_AREA="${STUDY_AREA_TYPE}_${SWAP_STUDY_AREA_CODE}_${STUDY_AREA_DEFINITION_VINTAGE}"
REFERENCE_OVERLAP="${CENSUS_GEOGRAPHY_TYPE}_in_${STUDY_AREA_TYPE}_${REFERENCE_STUDY_AREA_CODE}_${REFERENCE_CENSUS_GEOGRAPHY_YEAR}_${STUDY_AREA_DEFINITION_VINTAGE}_vintage"
SWAP_OVERLAP="${CENSUS_GEOGRAPHY_TYPE}_in_${STUDY_AREA_TYPE}_${SWAP_STUDY_AREA_CODE}_${SWAP_CENSUS_GEOGRAPHY_YEAR}_${STUDY_AREA_DEFINITION_VINTAGE}_vintage"
OUTPUT_SUFFIX="${STUDY_AREA_TYPE}_${CENSUS_GEOGRAPHY_TYPE}_${STUDY_AREA_DEFINITION_VINTAGE}"
CENSUS_GEOGRAPHY_YEARS_TAG="${CENSUS_GEOGRAPHY_YEARS_TAG:-$(printf "%s" "${CENSUS_GEOGRAPHY_YEARS}" | tr ' ' '-')}"
RUN_NAME="${RUN_NAME:-${CENSUS_GEOGRAPHY_TYPE}_in_${STUDY_AREA_TYPE}_${CENSUS_GEOGRAPHY_YEARS_TAG}_years_${STUDY_AREA_DEFINITION_VINTAGE}_vintage}"
RUN_OUTPUT_DIR="${RUN_OUTPUT_DIR:-outputs/${RUN_NAME}}"
RUN_LOG_FILE="${RUN_LOG_FILE:-${RUN_OUTPUT_DIR}/run.log}"
