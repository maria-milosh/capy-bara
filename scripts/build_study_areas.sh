#!/usr/bin/env bash

. scripts/pipeline_config.sh

python pipeline/build_study_areas.py \
    --filename "${STUDY_AREA_SOURCE_FILE}" \
    --definition-geographies "${STUDY_AREA_DEFINITION_GEOGRAPHIES}" \
    --study-area-type "${STUDY_AREA_TYPE}"
