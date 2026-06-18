import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


YEARS = ("1970", "1980", "1990", "2000", "2010", "2020")
NEW_ROOT = Path("cbsas")
OLD_ROOT = Path("old_cbsas")
DEFS_ROOT = Path("cbsas/defs")
OUT_ROOT = Path("points_vs_intersection_exploration")


def read_def_metadata():
    metadata = {}
    for path in DEFS_ROOT.glob("*.json"):
        with path.open() as f:
            payload = json.load(f)
        if isinstance(payload, str):
            payload = json.loads(payload)
        metadata[path.stem] = payload
    return metadata


def output_stem(path):
    stem = path.stem
    suffix = "_cbsa_tracts"
    if stem.endswith(suffix):
        return stem[: -len(suffix)]
    return stem


def read_outputs(root):
    outputs = defaultdict(dict)
    for year in YEARS:
        for path in sorted((root / year).glob("*.shp")):
            outputs[year][output_stem(path)] = path
    return outputs


def read_physical_files(root):
    files = defaultdict(dict)
    for year in YEARS:
        for path in sorted((root / year).glob("*")):
            if path.is_file():
                files[year][path.name] = path
    return files


def metadata_row(year, stem, status, path, metadata):
    info = metadata.get(stem, {})
    parts = stem.split("_", 2)
    filename_population = parts[0] if len(parts) > 0 else ""
    cbsa_code = parts[1] if len(parts) > 1 else info.get("cbsa_code", "")
    vintage = parts[2] if len(parts) > 2 else ""
    return {
        "year": year,
        "status": status,
        "stem": stem,
        "filename": path.name if path else "",
        "path": str(path) if path else "",
        "cbsa_code": info.get("cbsa_code", cbsa_code),
        "cbsa_title": info.get("cbsa_title", ""),
        "vintage": vintage,
        "filename_population": filename_population,
        "definition_population": info.get("total_population", ""),
        "component_counties_count": len(info.get("component_counties_fips", [])),
    }


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    metadata = read_def_metadata()
    old_outputs = read_outputs(OLD_ROOT)
    new_outputs = read_outputs(NEW_ROOT)
    old_physical = read_physical_files(OLD_ROOT)
    new_physical = read_physical_files(NEW_ROOT)

    detail_rows = []
    count_rows = []
    physical_detail_rows = []
    physical_count_rows = []
    physical_extension_count = Counter()
    missing_group = defaultdict(lambda: Counter({"missing_outputs": 0}))
    missing_cbsa_group = defaultdict(
        lambda: {
            "missing_outputs": 0,
            "titles": set(),
            "vintages": set(),
            "definition_populations": set(),
        }
    )
    vintage_group = Counter()

    for year in YEARS:
        old_stems = set(old_outputs[year])
        new_stems = set(new_outputs[year])
        old_only = sorted(old_stems - new_stems)
        new_only = sorted(new_stems - old_stems)
        common = old_stems & new_stems

        count_rows.append(
            {
                "year": year,
                "old_intersection_shp_count": len(old_stems),
                "new_points_shp_count": len(new_stems),
                "common_count": len(common),
                "missing_from_points_count": len(old_only),
                "new_only_count": len(new_only),
            }
        )

        for stem in old_only:
            row = metadata_row(
                year,
                stem,
                "missing_from_points",
                old_outputs[year][stem],
                metadata,
            )
            detail_rows.append(row)
            key = (
                year,
                row["cbsa_code"],
                row["cbsa_title"],
                row["definition_population"],
                row["component_counties_count"],
            )
            missing_group[key]["missing_outputs"] += 1
            cbsa_key = (year, row["cbsa_code"])
            missing_cbsa_group[cbsa_key]["missing_outputs"] += 1
            missing_cbsa_group[cbsa_key]["titles"].add(row["cbsa_title"])
            missing_cbsa_group[cbsa_key]["vintages"].add(row["vintage"])
            missing_cbsa_group[cbsa_key]["definition_populations"].add(
                str(row["definition_population"])
            )
            vintage_group[(year, row["vintage"])] += 1

        for stem in new_only:
            detail_rows.append(
                metadata_row(
                    year,
                    stem,
                    "new_points_only",
                    new_outputs[year][stem],
                    metadata,
                )
            )

        old_files = set(old_physical[year])
        new_files = set(new_physical[year])
        old_only_files = sorted(old_files - new_files)
        new_only_files = sorted(new_files - old_files)
        common_files = old_files & new_files
        physical_count_rows.append(
            {
                "year": year,
                "old_file_count": len(old_files),
                "new_file_count": len(new_files),
                "common_file_count": len(common_files),
                "old_only_file_count": len(old_only_files),
                "new_only_file_count": len(new_only_files),
            }
        )
        for name in old_only_files:
            suffix = Path(name).suffix or "<none>"
            physical_detail_rows.append(
                {
                    "year": year,
                    "status": "old_only",
                    "filename": name,
                    "extension": suffix,
                    "path": str(old_physical[year][name]),
                }
            )
            physical_extension_count[(year, "old_only", suffix)] += 1
        for name in new_only_files:
            suffix = Path(name).suffix or "<none>"
            physical_detail_rows.append(
                {
                    "year": year,
                    "status": "new_only",
                    "filename": name,
                    "extension": suffix,
                    "path": str(new_physical[year][name]),
                }
            )
            physical_extension_count[(year, "new_only", suffix)] += 1

    detail_fields = [
        "year",
        "status",
        "stem",
        "filename",
        "path",
        "cbsa_code",
        "cbsa_title",
        "vintage",
        "filename_population",
        "definition_population",
        "component_counties_count",
    ]
    write_csv(OUT_ROOT / "different_files.csv", detail_rows, detail_fields)

    write_csv(
        OUT_ROOT / "counts_by_year.csv",
        count_rows,
        [
            "year",
            "old_intersection_shp_count",
            "new_points_shp_count",
            "common_count",
            "missing_from_points_count",
            "new_only_count",
        ],
    )

    write_csv(
        OUT_ROOT / "physical_file_counts_by_year.csv",
        physical_count_rows,
        [
            "year",
            "old_file_count",
            "new_file_count",
            "common_file_count",
            "old_only_file_count",
            "new_only_file_count",
        ],
    )
    write_csv(
        OUT_ROOT / "different_physical_files.csv",
        physical_detail_rows,
        ["year", "status", "filename", "extension", "path"],
    )
    physical_extension_rows = [
        {
            "year": year,
            "status": status,
            "extension": extension,
            "file_count": count,
        }
        for (year, status, extension), count in sorted(physical_extension_count.items())
    ]
    write_csv(
        OUT_ROOT / "physical_file_differences_by_year_extension.csv",
        physical_extension_rows,
        ["year", "status", "extension", "file_count"],
    )

    missing_rows = []
    for (
        year,
        cbsa_code,
        cbsa_title,
        definition_population,
        component_counties_count,
    ), counts in missing_group.items():
        missing_rows.append(
            {
                "year": year,
                "cbsa_code": cbsa_code,
                "cbsa_title": cbsa_title,
                "definition_population": definition_population,
                "component_counties_count": component_counties_count,
                "missing_outputs": counts["missing_outputs"],
            }
        )

    missing_rows.sort(
        key=lambda row: (
            row["year"],
            -row["missing_outputs"],
            row["cbsa_title"],
            row["cbsa_code"],
        )
    )
    write_csv(
        OUT_ROOT / "missing_metro_areas_by_year.csv",
        missing_rows,
        [
            "year",
            "cbsa_code",
            "cbsa_title",
            "definition_population",
            "component_counties_count",
            "missing_outputs",
        ],
    )

    missing_cbsa_rows = []
    for (year, cbsa_code), values in missing_cbsa_group.items():
        missing_cbsa_rows.append(
            {
                "year": year,
                "cbsa_code": cbsa_code,
                "cbsa_titles": "|".join(sorted(values["titles"])),
                "definition_populations": "|".join(
                    sorted(values["definition_populations"])
                ),
                "vintages": "|".join(sorted(values["vintages"])),
                "missing_outputs": values["missing_outputs"],
            }
        )
    missing_cbsa_rows.sort(
        key=lambda row: (
            row["year"],
            -row["missing_outputs"],
            row["cbsa_titles"],
            row["cbsa_code"],
        )
    )
    write_csv(
        OUT_ROOT / "missing_cbsa_codes_by_year.csv",
        missing_cbsa_rows,
        [
            "year",
            "cbsa_code",
            "cbsa_titles",
            "definition_populations",
            "vintages",
            "missing_outputs",
        ],
    )

    vintage_rows = [
        {"year": year, "vintage": vintage, "missing_outputs": count}
        for (year, vintage), count in sorted(vintage_group.items())
    ]
    write_csv(
        OUT_ROOT / "missing_by_year_and_vintage.csv",
        vintage_rows,
        ["year", "vintage", "missing_outputs"],
    )

    readme = OUT_ROOT / "README.md"
    readme.write_text(
        "# Points vs. Intersection Exploration\n\n"
        "Generated comparison outputs for `cbsas` "
        "(representative-point selection) and `old_cbsas` "
        "(polygon-intersection selection).\n\n"
        "- `counts_by_year.csv`: total `.shp` outputs by year and status.\n"
        "- `different_files.csv`: one row per output present in one tree but not the other.\n"
        "- `physical_file_counts_by_year.csv`: raw filesystem counts by year.\n"
        "- `different_physical_files.csv`: one row per physical file present in only "
        "one tree.\n"
        "- `physical_file_differences_by_year_extension.csv`: physical-file "
        "differences grouped by extension.\n"
        "- `missing_metro_areas_by_year.csv`: old-intersection outputs absent from "
        "the representative-point outputs, grouped by year and CBSA.\n"
        "- `missing_cbsa_codes_by_year.csv`: same missing outputs grouped only by "
        "year and CBSA code, with titles/vintages collapsed.\n"
        "- `missing_by_year_and_vintage.csv`: missing outputs grouped by year and "
        "CBSA definition vintage.\n"
        "- `missing_old_file_stats.csv`: row counts, states, counties, and total "
        "population for old-intersection outputs absent from `cbsas`.\n"
        "- `missing_old_file_row_count_summary.csv`: row-count summary for missing "
        "old outputs by year.\n"
        "- `missing_old_files_by_year_and_state.csv`: state breakdown of missing "
        "old output contents.\n"
        "- `processed_tract_state_counts.csv`: state coverage of the current "
        "`processed/*_tracts.shp` files.\n"
    )


if __name__ == "__main__":
    main()
