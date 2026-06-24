#!/usr/bin/env bash

# Set up folder structure
CENSUS_GEOGRAPHY_YEARS="${CENSUS_GEOGRAPHY_YEARS:-2020 2010 2000 1990 1980 1970}"

mkdir -p study_area_sources
mkdir -p nhgis
mkdir -p study_areas

mkdir -p study_areas/definitions
for year in ${CENSUS_GEOGRAPHY_YEARS}; do
    mkdir -p "study_areas/${year}"
done

mkdir -p outputs
mkdir -p figures
mkdir -p census_geographies
