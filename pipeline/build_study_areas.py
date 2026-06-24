# try:
#     from .definitions import CBSA, CBSADict
# except ImportError:
from definitions import CBSA, CBSADict

import multiprocessing
from shapely.ops import unary_union
from typing import Dict
import tqdm
import pandas as pd
import typer
import geopandas as gpd
import json
import os
from pathlib import Path


def main(
    filename: str = "study_area_sources/list1_march_2020.xls",
    definition_geographies: str = "census_geographies/2020_tracts.shp",
    output_dir: str = "study_areas/definitions",
    study_area_type: str = "cbsa",
):
    source_stem = Path(filename).stem
    if study_area_type == "cbsa" and source_stem.startswith("list1_"):
        definition_vintage = source_stem.removeprefix("list1_")
    elif source_stem.startswith(f"{study_area_type}_"):
        definition_vintage = source_stem.removeprefix(f"{study_area_type}_")
    else:
        definition_vintage = source_stem

    metro_areas = fetch_metro_areas(filename)
    mappings_without_pops = create_metro_mappings(metro_areas)
    # mappings_without_pops = dict(list(mappings_without_pops.items())[:3])
    country = gpd.read_file(definition_geographies)
    country["STATEFP"] = country["STATEFP"].apply(lambda x: str(x).zfill(2))
    country["COUNTYFP"] = country["COUNTYFP"].apply(lambda x: str(x).zfill(3))
    country["STCNTYFP"] = country["STATEFP"] + country["COUNTYFP"]

    metros = {
        k: add_cbsa_pop_and_geometry(country, v)
        for k, v in tqdm.tqdm(mappings_without_pops.items())
    }
    # with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
    #     f = lambda x: (x[0], add_cbsa_pop_and_geometry(country, x[1]))
    #     metros_with_pops = dict(p.imap(f, mappings_without_pops.items()))

    for cbsa_code, cbsa in metros.items():
        output_stem = f"{study_area_type}_{cbsa_code}_{definition_vintage}"
        with open(
            f"{output_dir}/{output_stem}.json",
            "w",
        ) as w:
            json.dump(cbsa.json(exclude={"geometry": True}), w)

        try:
            cbsa.geometry.to_file(f"{output_dir}/{output_stem}.shp")
        except ValueError as e:
            print(f"{output_dir}/{output_stem}.shp")
            raise


def fetch_metro_areas(filename) -> pd.DataFrame:
    cbsa_counties = pd.read_excel(filename, skiprows=2)
    cbsa_counties = cbsa_counties[~cbsa_counties["FIPS County Code"].isna()]
    cbsa_counties["FIPS County Code"] = (
        cbsa_counties["FIPS County Code"]
        .astype(int)
        .astype(str)
        .apply(lambda x: x.zfill(3))
    )
    cbsa_counties["FIPS State Code"] = (
        cbsa_counties["FIPS State Code"]
        .astype(int)
        .astype(str)
        .apply(lambda x: x.zfill(2))
    )
    metro_areas = cbsa_counties[
        cbsa_counties["Metropolitan/Micropolitan Statistical Area"]
        == "Metropolitan Statistical Area"
    ]
    return metro_areas


def create_metro_mappings(metro_areas: pd.DataFrame) -> Dict[str, CBSA]:
    metro_mappings = {}
    for c, row in metro_areas.iterrows():
        cbsa_code = row["CBSA Code"]
        cbsa_title = row["CBSA Title"]
        fips_code = row["FIPS State Code"] + row["FIPS County Code"]
        if cbsa_code in metro_mappings:
            metro_mappings[cbsa_code].component_counties_fips.append(fips_code)
        else:
            metro_mappings[cbsa_code] = CBSA(
                cbsa_code=cbsa_code,
                cbsa_title=cbsa_title,
                component_counties_fips=[fips_code],
                total_population=None,
            )

    return metro_mappings


def add_cbsa_pop_and_geometry(country: gpd.GeoDataFrame, cbsa: CBSA) -> CBSA:
    assert cbsa.total_population == None

    cbsa_components = country[
        country["STCNTYFP"].apply(lambda x: x in cbsa.component_counties_fips)
    ]

    cbsa.geometry = cbsa_components.dissolve()
    cbsa.total_population = int(cbsa_components["TOTPOP"].sum())

    assert cbsa.total_population != None

    return cbsa


if __name__ == "__main__":
    typer.run(main)
