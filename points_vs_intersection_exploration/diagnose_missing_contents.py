import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import geopandas as gpd


YEARS = ("1970", "1980", "1990", "2000", "2010", "2020")
OUT_ROOT = Path("points_vs_intersection_exploration")


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def state_column(frame):
    if "STATE" in frame.columns:
        return "STATE"
    for candidate in ("STATEFP", "STATEFP10", "STATEFP_df"):
        if candidate in frame.columns:
            return candidate
    return None


def county_column(frame):
    if "COUNTY" in frame.columns:
        return "COUNTY"
    if "COUNTY_df" in frame.columns:
        return "COUNTY_df"
    return None


def main():
    with (OUT_ROOT / "different_files.csv").open() as f:
        missing_rows = [
            row
            for row in csv.DictReader(f)
            if row["status"] == "missing_from_points"
        ]

    file_stats = []
    state_file_counts = Counter()
    state_row_counts = Counter()

    for row in missing_rows:
        frame = gpd.read_file(row["path"], ignore_geometry=True)
        states_col = state_column(frame)
        counties_col = county_column(frame)
        states = sorted(str(value) for value in frame[states_col].dropna().unique()) if states_col else []
        counties = (
            sorted(str(value) for value in frame[counties_col].dropna().unique())
            if counties_col
            else []
        )
        total_pop = int(frame["TOTPOP"].sum()) if "TOTPOP" in frame.columns else ""
        file_stats.append(
            {
                "year": row["year"],
                "stem": row["stem"],
                "cbsa_code": row["cbsa_code"],
                "cbsa_title": row["cbsa_title"],
                "vintage": row["vintage"],
                "row_count": len(frame),
                "total_pop_in_old_output": total_pop,
                "states": "|".join(states),
                "state_count": len(states),
                "counties": "|".join(counties),
                "county_count": len(counties),
                "path": row["path"],
            }
        )

        for state in states:
            state_file_counts[(row["year"], state)] += 1
            state_row_counts[(row["year"], state)] += int((frame[states_col] == state).sum())

    write_csv(
        OUT_ROOT / "missing_old_file_stats.csv",
        file_stats,
        [
            "year",
            "stem",
            "cbsa_code",
            "cbsa_title",
            "vintage",
            "row_count",
            "total_pop_in_old_output",
            "states",
            "state_count",
            "counties",
            "county_count",
            "path",
        ],
    )

    summary_rows = []
    for year in YEARS:
        counts = [row["row_count"] for row in file_stats if row["year"] == year]
        if counts:
            summary_rows.append(
                {
                    "year": year,
                    "missing_files": len(counts),
                    "old_output_rows_total": sum(counts),
                    "min_rows": min(counts),
                    "median_rows": statistics.median(counts),
                    "mean_rows": round(statistics.mean(counts), 2),
                    "max_rows": max(counts),
                }
            )
        else:
            summary_rows.append(
                {
                    "year": year,
                    "missing_files": 0,
                    "old_output_rows_total": 0,
                    "min_rows": "",
                    "median_rows": "",
                    "mean_rows": "",
                    "max_rows": "",
                }
            )

    write_csv(
        OUT_ROOT / "missing_old_file_row_count_summary.csv",
        summary_rows,
        [
            "year",
            "missing_files",
            "old_output_rows_total",
            "min_rows",
            "median_rows",
            "mean_rows",
            "max_rows",
        ],
    )

    state_rows = [
        {
            "year": year,
            "state": state,
            "missing_files_with_state": state_file_counts[(year, state)],
            "old_output_rows_with_state": state_row_counts[(year, state)],
        }
        for year, state in sorted(state_file_counts)
    ]
    write_csv(
        OUT_ROOT / "missing_old_files_by_year_and_state.csv",
        state_rows,
        [
            "year",
            "state",
            "missing_files_with_state",
            "old_output_rows_with_state",
        ],
    )

    processed_rows = []
    for year in YEARS:
        path = Path(f"processed/{year}_tracts.shp")
        frame = gpd.read_file(path, ignore_geometry=True)
        states_col = state_column(frame)
        statefp_col = "STATEFP"
        if "STATEFP_df" in frame.columns:
            statefp_col = "STATEFP_df"
        if "STATEFP10" in frame.columns:
            statefp_col = "STATEFP10"
        grouped = frame.groupby([statefp_col, states_col], dropna=False).size()
        for (statefp, state), tract_rows in grouped.items():
            processed_rows.append(
                {
                    "year": year,
                    "statefp": statefp,
                    "state": state,
                    "processed_tract_rows": tract_rows,
                }
            )

    write_csv(
        OUT_ROOT / "processed_tract_state_counts.csv",
        processed_rows,
        ["year", "statefp", "state", "processed_tract_rows"],
    )


if __name__ == "__main__":
    main()
