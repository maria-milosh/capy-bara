import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd


EXPLORATION_ROOT = Path("points_vs_intersection_exploration")
DEFS_ROOT = Path("cbsas/defs")
DEFAULT_VINTAGE = "march_2020"
YEARS = ("1970", "1980", "1990", "2000", "2010", "2020")
ID_COLUMNS = ("GISJOIN", "GEOID", "NHGISCODE")
DETAIL_COLUMNS = (
    "year",
    "stem",
    "cbsa_code",
    "cbsa_title",
    "vintage",
    "tract_id_column",
    "tract_id",
    "source_path",
    "definition_path",
    "state",
    "county",
    "tract_name",
    "total_population",
    "tract_area_sq_m",
    "tract_area_sq_km",
    "cbsa_overlap_area_sq_m",
    "cbsa_overlap_area_sq_km",
    "cbsa_overlap_pct_of_tract",
    "positive_area_overlap",
    "representative_point_within_cbsa",
)
SUMMARY_COLUMNS = (
    "summary_level",
    "year",
    "stem",
    "cbsa_code",
    "cbsa_title",
    "vintage",
    "excluded_tract_count",
    "positive_area_overlap_tract_count",
    "zero_area_overlap_tract_count",
    "total_overlap_area_sq_m",
    "mean_overlap_area_sq_m",
    "mean_overlap_area_sq_km",
    "median_overlap_area_sq_m",
    "max_overlap_area_sq_m",
    "max_overlap_area_sq_km",
    "mean_overlap_pct_of_tract",
    "median_overlap_pct_of_tract",
    "max_overlap_pct_of_tract",
    "mean_positive_overlap_area_sq_m",
    "mean_positive_overlap_area_sq_km",
    "max_overlap_tract_id",
    "max_overlap_state",
    "max_overlap_county",
    "max_overlap_tract_name",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Measure CBSA boundary overlap for tracts excluded by the "
            "representative-point assignment method."
        )
    )
    parser.add_argument(
        "--membership-csv",
        type=Path,
        default=EXPLORATION_ROOT / "tract_membership_changes.csv",
    )
    parser.add_argument("--defs-root", type=Path, default=DEFS_ROOT)
    parser.add_argument("--out-root", type=Path, default=EXPLORATION_ROOT)
    parser.add_argument("--vintage", default=DEFAULT_VINTAGE)
    parser.add_argument("--years", nargs="*", default=YEARS)
    parser.add_argument(
        "--detail-csv",
        type=Path,
        default=None,
        help="Defaults to OUT_ROOT/excluded_tract_overlap_areas.csv.",
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=None,
        help="Defaults to OUT_ROOT/excluded_tract_overlap_summary.csv.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    detail_csv = args.detail_csv or args.out_root / "excluded_tract_overlap_areas.csv"
    summary_csv = (
        args.summary_csv or args.out_root / "excluded_tract_overlap_summary.csv"
    )

    membership = read_removed_membership(args.membership_csv, args.vintage, args.years)
    detail = calculate_detail_rows(membership, args.defs_root)
    summary = calculate_summary_rows(detail)

    args.out_root.mkdir(parents=True, exist_ok=True)
    detail.to_csv(detail_csv, index=False, columns=DETAIL_COLUMNS)
    summary.to_csv(summary_csv, index=False, columns=SUMMARY_COLUMNS)

    print(detail_csv)
    print(summary_csv)


def read_removed_membership(path, vintage, years):
    membership = pd.read_csv(
        path,
        dtype={
            "year": str,
            "stem": str,
            "cbsa_code": str,
            "vintage": str,
            "change_type": str,
            "source_path": str,
            "tract_id_column": str,
            "tract_id": str,
        },
    )
    removed = membership[membership["change_type"] == "removed_by_points"].copy()
    if vintage:
        removed = removed[removed["vintage"] == vintage]
    if years:
        removed = removed[removed["year"].isin({str(year) for year in years})]
    return removed


def calculate_detail_rows(membership, defs_root):
    rows = []
    for (year, stem, source_path), group in membership.groupby(
        ["year", "stem", "source_path"], sort=True
    ):
        source_path = Path(source_path)
        definition_path = defs_root / f"{stem}.shp"
        tracts = gpd.read_file(source_path)
        definition = gpd.read_file(definition_path).to_crs(tracts.crs)
        definition_geometry = union_geometry(definition)
        id_column = choose_id_column(tracts, group["tract_id_column"].iloc[0])
        tracts = with_clean_id(tracts, id_column)

        for _, membership_row in group.iterrows():
            tract_id = clean_value(membership_row["tract_id"])
            matches = tracts[tracts["_clean_id"] == tract_id]
            if matches.empty:
                raise ValueError(
                    f"Could not find tract {tract_id} in {source_path}"
                )
            for _, tract in matches.iterrows():
                rows.append(
                    detail_row(
                        membership_row,
                        tract,
                        id_column,
                        source_path,
                        definition_path,
                        definition_geometry,
                    )
                )

    return pd.DataFrame(rows, columns=DETAIL_COLUMNS)


def detail_row(
    membership_row,
    tract,
    id_column,
    source_path,
    definition_path,
    definition_geometry,
):
    tract_geometry = tract.geometry
    tract_area = float(tract_geometry.area)
    overlap_area = float(tract_geometry.intersection(definition_geometry).area)
    representative_point = tract_geometry.representative_point()

    return {
        "year": membership_row["year"],
        "stem": membership_row["stem"],
        "cbsa_code": membership_row["cbsa_code"],
        "cbsa_title": membership_row["cbsa_title"],
        "vintage": membership_row["vintage"],
        "tract_id_column": id_column,
        "tract_id": clean_value(membership_row["tract_id"]),
        "source_path": str(source_path),
        "definition_path": str(definition_path),
        "state": first_available_value_from_rows(
            (tract, membership_row), ("STATE", "STATENH")
        ),
        "county": first_available_value_from_rows(
            (tract, membership_row), ("COUNTY_df", "COUNTYNH", "COUNTY")
        ),
        "tract_name": first_available_value_from_rows(
            (tract, membership_row), ("NAMELSAD", "NAME_df", "NAME", "TRACTA")
        ),
        "total_population": numeric_value(membership_row.get("TOTPOP")),
        "tract_area_sq_m": tract_area,
        "tract_area_sq_km": tract_area / 1_000_000,
        "cbsa_overlap_area_sq_m": overlap_area,
        "cbsa_overlap_area_sq_km": overlap_area / 1_000_000,
        "cbsa_overlap_pct_of_tract": pct(overlap_area, tract_area),
        "positive_area_overlap": overlap_area > 0,
        "representative_point_within_cbsa": bool(
            definition_geometry.contains(representative_point)
        ),
    }


def calculate_summary_rows(detail):
    if detail.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    groups = [("overall", []), ("year", ["year"]), ("year_cbsa", ["year", "stem"])]
    rows = []
    for summary_level, group_columns in groups:
        if group_columns:
            grouped = detail.groupby(group_columns, sort=True, dropna=False)
            for _, group in grouped:
                rows.append(summary_row(summary_level, group))
        else:
            rows.append(summary_row(summary_level, detail))

    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def summary_row(summary_level, group):
    max_index = group["cbsa_overlap_area_sq_m"].idxmax()
    max_row = group.loc[max_index]
    positive = group[group["cbsa_overlap_area_sq_m"] > 0]
    positive_mean_sq_m = positive["cbsa_overlap_area_sq_m"].mean()

    return {
        "summary_level": summary_level,
        "year": group_value(group, "year", summary_level != "overall"),
        "stem": group_value(group, "stem", summary_level == "year_cbsa"),
        "cbsa_code": group_value(group, "cbsa_code", summary_level == "year_cbsa"),
        "cbsa_title": group_value(group, "cbsa_title", summary_level == "year_cbsa"),
        "vintage": group_value(group, "vintage", summary_level != "overall"),
        "excluded_tract_count": len(group),
        "positive_area_overlap_tract_count": int(
            group["positive_area_overlap"].sum()
        ),
        "zero_area_overlap_tract_count": int((~group["positive_area_overlap"]).sum()),
        "total_overlap_area_sq_m": group["cbsa_overlap_area_sq_m"].sum(),
        "mean_overlap_area_sq_m": group["cbsa_overlap_area_sq_m"].mean(),
        "mean_overlap_area_sq_km": group["cbsa_overlap_area_sq_km"].mean(),
        "median_overlap_area_sq_m": group["cbsa_overlap_area_sq_m"].median(),
        "max_overlap_area_sq_m": max_row["cbsa_overlap_area_sq_m"],
        "max_overlap_area_sq_km": max_row["cbsa_overlap_area_sq_km"],
        "mean_overlap_pct_of_tract": group["cbsa_overlap_pct_of_tract"].mean(),
        "median_overlap_pct_of_tract": group[
            "cbsa_overlap_pct_of_tract"
        ].median(),
        "max_overlap_pct_of_tract": max_row["cbsa_overlap_pct_of_tract"],
        "mean_positive_overlap_area_sq_m": positive_mean_sq_m,
        "mean_positive_overlap_area_sq_km": positive_mean_sq_m / 1_000_000,
        "max_overlap_tract_id": max_row["tract_id"],
        "max_overlap_state": max_row["state"],
        "max_overlap_county": max_row["county"],
        "max_overlap_tract_name": max_row["tract_name"],
    }


def group_value(group, column, include):
    if not include:
        return ""
    values = group[column].dropna().astype(str).unique()
    if len(values) == 1:
        return values[0]
    return ";".join(sorted(values))


def choose_id_column(tracts, preferred):
    if preferred in tracts.columns:
        return preferred
    for column in ID_COLUMNS:
        if column in tracts.columns:
            return column
    raise ValueError("Expected a tract identifier column")


def with_clean_id(frame, id_column):
    frame = frame.copy()
    frame["_clean_id"] = frame[id_column].astype(str).str.strip()
    return frame


def union_geometry(frame):
    geometry = frame.geometry
    if hasattr(geometry, "union_all"):
        return geometry.union_all()
    return geometry.unary_union


def first_available_value(row, columns):
    for column in columns:
        if column in row.index:
            value = row[column]
            if pd.notna(value):
                return str(value).strip()
    return ""


def first_available_value_from_rows(rows, columns):
    for row in rows:
        value = first_available_value(row, columns)
        if value:
            return value
    return ""


def clean_value(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def numeric_value(value):
    if value is None or pd.isna(value):
        return ""
    return int(value)


def pct(numerator, denominator):
    if denominator == 0:
        return ""
    return numerator / denominator * 100


if __name__ == "__main__":
    main()
