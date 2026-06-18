import argparse
import os
from pathlib import Path

MPLCONFIGDIR = Path("/private/tmp/capy-bara-matplotlib")
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MaxNLocator


matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXPLORATION_ROOT = Path("points_vs_intersection_exploration")
FIGURE_ROOT = EXPLORATION_ROOT / "figures"
DEFAULT_VINTAGE = "march_2020"
DEFAULT_CBSA_CODE = "16980"
DEFAULT_MAP_YEARS = ("1970", "1980", "1990", "2000", "2010", "2020")
LARGE_EXCLUDED_OVERLAP_EXAMPLES = (
    {
        "year": "1980",
        "cbsa_code": "49740",
        "vintage": "march_2020",
        "tract_id": "G04002700105",
    },
    {
        "year": "1980",
        "cbsa_code": "49740",
        "vintage": "march_2020",
        "tract_id": "G04002700107",
    },
    {
        "year": "1980",
        "cbsa_code": "15180",
        "vintage": "march_2020",
        "tract_id": "G4800610012302",
    },
)

COUNT_COLUMNS = (
    ("old_intersection_shp_count", "Old intersection method"),
    ("new_points_shp_count", "Representative-point method"),
)
COUNT_COLORS = {
    "Old intersection method": "#C85A27",
    "Representative-point method": "#157A6E",
}
MAP_COLORS = {
    "outline": "#2F3437",
    "retained": "#EFEFEF",
    "retained_edge": "#B8B8B8",
    "removed": "#D95F02",
    "removed_edge": "#8C2D04",
    "added": "#1B9E77",
    "added_edge": "#0B5D4C",
}
ID_COLUMNS = ("GISJOIN", "GEOID", "NHGISCODE")
RACE_COLUMNS = ("WHITE", "BLACK", "AMIN", "ASIAN", "2MORE", "POC")
RACE_LABELS = {
    "WHITE": "White",
    "BLACK": "Black",
    "AMIN": "American Indian",
    "ASIAN": "Asian",
    "2MORE": "Two or more",
    "POC": "POC (derived)",
}
RACE_COLORS = {
    "WHITE": "#4C78A8",
    "BLACK": "#F58518",
    "AMIN": "#54A24B",
    "ASIAN": "#B279A2",
    "2MORE": "#E45756",
    "POC": "#72B7B2",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate comparison figures for representative points vs. intersections."
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=EXPLORATION_ROOT / "assignment_summary_by_year.csv",
    )
    parser.add_argument(
        "--comparison-csv",
        type=Path,
        default=EXPLORATION_ROOT / "assignment_comparison_by_cbsa.csv",
    )
    parser.add_argument(
        "--overlap-csv",
        type=Path,
        default=EXPLORATION_ROOT / "excluded_tract_overlap_areas.csv",
    )
    parser.add_argument("--defs-root", type=Path, default=Path("cbsas/defs"))
    parser.add_argument("--figure-root", type=Path, default=FIGURE_ROOT)
    parser.add_argument("--vintage", default=DEFAULT_VINTAGE)
    parser.add_argument("--cbsa-code", default=DEFAULT_CBSA_CODE)
    parser.add_argument("--map-years", nargs="*", default=DEFAULT_MAP_YEARS)
    return parser.parse_args()


def main():
    args = parse_args()
    args.figure_root.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(args.summary_csv, dtype={"year": str})
    comparison = pd.read_csv(
        args.comparison_csv,
        dtype={"year": str, "cbsa_code": str, "stem": str, "vintage": str},
    )
    overlap = pd.read_csv(args.overlap_csv, dtype={"year": str})

    outputs = [
        plot_metro_counts(summary, args.figure_root / "metro_counts_by_year.png"),
        plot_chicago_difference_tiles(
            comparison,
            args.figure_root,
            args.cbsa_code,
            args.vintage,
            args.map_years,
            args.defs_root,
        ),
        plot_chicago_positive_overlap_example(
            comparison,
            args.figure_root,
            args.cbsa_code,
            args.vintage,
            args.defs_root,
        ),
        plot_tract_count_distributions(
            comparison, args.figure_root / "tract_count_distributions.png"
        ),
        plot_total_population_changes(
            comparison, args.figure_root / "total_population_changes.png"
        ),
        plot_total_population_scatter_by_year(
            comparison, args.figure_root / "total_population_scatter_by_year.png"
        ),
        plot_race_population_changes(
            summary, args.figure_root / "race_population_changes.png"
        ),
        plot_race_removed_percentages_by_year(
            comparison,
            args.figure_root / "race_removed_percentages_by_year.png",
        ),
        plot_race_population_outliers(
            comparison, args.figure_root / "race_population_outliers.png"
        ),
        plot_excluded_overlap_distribution(
            overlap,
            args.figure_root / "excluded_tract_overlap_distribution.png",
        ),
        plot_large_excluded_overlap_examples(
            comparison,
            args.figure_root / "large_excluded_overlap_examples_1980.png",
            args.defs_root,
        ),
    ]

    for path in outputs:
        print(path)


def plot_metro_counts(summary, output_path):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    plot_grouped_count_bars(ax, summary, COUNT_COLUMNS)
    handles = [
        Patch(facecolor=COUNT_COLORS[label], label=label)
        for _, label in COUNT_COLUMNS
    ]
    ax.legend(
        handles=handles,
        loc="upper left",
        frameon=False,
    )
    ax.set_title("Metro counts per year", fontsize=14)
    ax.set_xlabel("Tract data year")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_grouped_count_bars(ax, frame, columns):
    years = frame["year"].tolist()
    x_positions = np.arange(len(years))
    width = 0.32
    offsets = np.linspace(-width / 2, width / 2, len(columns))

    for offset, (column, label) in zip(offsets, columns):
        values = frame[column].fillna(0).astype(int).to_numpy()
        bars = ax.bar(
            x_positions + offset,
            values,
            width=width,
            color=COUNT_COLORS[label],
            label=label,
        )
        for bar, value in zip(bars, values):
            if value == 0:
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 5,
                f"{value:,}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax.set_ylabel("Metro count")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(years)
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.margins(y=0.16)


def plot_tract_count_distributions(comparison, output_path):
    common = comparison[comparison["status"] == "common"].copy()
    old_counts = numeric_series(common, "old_tract_count")
    new_counts = numeric_series(common, "new_tract_count")
    deltas = numeric_series(common, "tract_count_delta")
    shared_bins = np.linspace(0, max(old_counts.max(), new_counts.max()), 42)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    plot_tract_count_histogram(
        axes[0, 0],
        old_counts,
        shared_bins,
        "Old intersection method",
        COUNT_COLORS["Old intersection method"],
    )
    plot_tract_count_histogram(
        axes[0, 1],
        new_counts,
        shared_bins,
        "Representative-point method",
        COUNT_COLORS["Representative-point method"],
    )
    shared_ymax = max(axes[0, 0].get_ylim()[1], axes[0, 1].get_ylim()[1])
    axes[0, 0].set_ylim(0, shared_ymax)
    axes[0, 1].set_ylim(0, shared_ymax)

    plot_tract_count_delta_histogram(axes[1, 0], deltas)
    plot_old_only_tract_counts(axes[1, 1], comparison)

    fig.suptitle("Tract count distributions", fontsize=15)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def numeric_series(frame, column):
    return pd.to_numeric(frame[column], errors="coerce").dropna()


def plot_tract_count_histogram(ax, values, bins, title, color):
    ax.hist(values, bins=bins, color=color, edgecolor="white", linewidth=0.4)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Tracts per common metro area")
    ax.set_ylabel("Metro count")
    ax.set_xlim(bins[0], bins[-1])
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_tract_count_delta_histogram(ax, deltas):
    minimum = int(np.floor(deltas.min() / 5) * 5)
    bins = np.arange(minimum - 0.5, 1.5, 5)
    ax.hist(deltas, bins=bins, color="#6E7781", edgecolor="white", linewidth=0.4)
    ax.axvline(0, color="#2F3437", linewidth=1)
    ax.set_title("Common metro tract-count delta", fontsize=11)
    ax.set_xlabel("Representative-point tracts minus old-intersection tracts")
    ax.set_ylabel("Metro count")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_old_only_tract_counts(ax, comparison):
    old_only = comparison[comparison["status"] == "old_only"].copy()
    if old_only.empty:
        ax.text(
            0.5,
            0.5,
            "No old-only metro areas",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        ax.axis("off")
        return

    old_only["old_tract_count"] = pd.to_numeric(
        old_only["old_tract_count"], errors="coerce"
    ).fillna(0)
    grouped = (
        old_only.groupby("year", as_index=False)
        .agg(metro_count=("stem", "count"), tract_count=("old_tract_count", "sum"))
        .sort_values("year")
    )
    bars = ax.bar(
        grouped["year"],
        grouped["metro_count"],
        color="#B33A3A",
        edgecolor="white",
        linewidth=0.4,
    )
    for bar, (_, row) in zip(bars, grouped.iterrows()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{int(row['metro_count']):,} metros\n{int(row['tract_count']):,} tracts",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_title("Old-only outputs kept separate", fontsize=11)
    ax.set_xlabel("Tract data year")
    ax.set_ylabel("Old-only metro count")
    ax.set_ylim(0, max(grouped["metro_count"]) * 1.35)
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def common_population_frame(comparison):
    common = comparison[comparison["status"] == "common"].copy()
    columns = (
        "old_total_population",
        "new_total_population",
        "population_delta",
        "population_pct_delta",
    )
    for column in columns:
        common[column] = pd.to_numeric(common[column], errors="coerce")
    return common.dropna(subset=list(columns))


def plot_total_population_changes(comparison, output_path):
    common = common_population_frame(comparison)
    old_pop = common["old_total_population"]
    new_pop = common["new_total_population"]
    deltas = common["population_delta"]
    removed = -deltas[deltas < 0]
    pct_removed = -common.loc[common["population_pct_delta"] < 0, "population_pct_delta"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    plot_total_population_overlay_histogram(axes[0, 0], old_pop, new_pop)
    plot_population_delta_histogram(axes[0, 1], deltas)
    plot_removed_population_histogram(axes[1, 0], removed)
    plot_removed_population_pct_histogram(axes[1, 1], pct_removed)

    fig.suptitle("Total population changes", fontsize=15)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_total_population_overlay_histogram(ax, old_pop, new_pop):
    values = pd.concat([old_pop, new_pop])
    bins = np.logspace(np.floor(np.log10(values.min())), np.ceil(np.log10(values.max())), 48)
    ax.hist(
        old_pop,
        bins=bins,
        color=COUNT_COLORS["Old intersection method"],
        alpha=0.55,
        edgecolor="white",
        linewidth=0.25,
        label="Old intersection",
    )
    ax.hist(
        new_pop,
        bins=bins,
        color=COUNT_COLORS["Representative-point method"],
        alpha=0.55,
        edgecolor="white",
        linewidth=0.25,
        label="Representative points",
    )
    ax.set_xscale("log")
    ax.set_title("Total population distribution", fontsize=11)
    ax.set_xlabel("Total population per common metro area")
    ax.set_ylabel("Metro count")
    ax.legend(frameon=False, fontsize=9)
    style_distribution_axis(ax)


def plot_population_delta_histogram(ax, deltas):
    bins = np.linspace(deltas.min(), 0, 54)
    ax.hist(deltas, bins=bins, color="#6E7781", edgecolor="white", linewidth=0.35)
    ax.axvline(0, color="#2F3437", linewidth=1)
    ax.set_title("Population delta", fontsize=11)
    ax.set_xlabel("Representative-point population minus old-intersection population")
    ax.set_ylabel("Metro count")
    style_distribution_axis(ax)


def plot_removed_population_histogram(ax, removed):
    bins = np.logspace(0, np.ceil(np.log10(removed.max())), 54)
    ax.hist(
        removed,
        bins=bins,
        color=MAP_COLORS["removed"],
        edgecolor="white",
        linewidth=0.35,
    )
    ax.set_xscale("log")
    ax.set_title("Population removed, changed pairs only", fontsize=11)
    ax.set_xlabel("Old population minus representative-point population")
    ax.set_ylabel("Metro count")
    style_distribution_axis(ax)


def plot_removed_population_pct_histogram(ax, pct_removed):
    bins = np.logspace(
        np.floor(np.log10(pct_removed.min())),
        np.ceil(np.log10(pct_removed.max())),
        54,
    )
    ax.hist(
        pct_removed,
        bins=bins,
        color="#B33A3A",
        edgecolor="white",
        linewidth=0.35,
    )
    ax.set_xscale("log")
    ax.set_title("Percent population removed, changed pairs only", fontsize=11)
    ax.set_xlabel("Percent decrease from old-intersection population")
    ax.set_ylabel("Metro count")
    style_distribution_axis(ax)


def plot_total_population_scatter_by_year(comparison, output_path):
    common = common_population_frame(comparison)
    years = sorted(common["year"].unique())
    all_values = pd.concat(
        [common["old_total_population"], common["new_total_population"]]
    )
    lower = 10 ** np.floor(np.log10(all_values.min()))
    upper = 10 ** np.ceil(np.log10(all_values.max()))

    fig, axes = plt.subplots(2, 3, figsize=(12, 8.4), constrained_layout=True)
    for ax, year in zip(axes.ravel(), years):
        year_rows = common[common["year"] == year]
        ax.scatter(
            year_rows["old_total_population"],
            year_rows["new_total_population"],
            s=11,
            alpha=0.45,
            color=COUNT_COLORS["Representative-point method"],
            linewidth=0,
        )
        ax.plot([lower, upper], [lower, upper], color="#2F3437", linewidth=0.9)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(lower, upper)
        ax.set_ylim(lower, upper)
        ax.set_title(f"{year}\n{len(year_rows):,} common metro areas", fontsize=10)
        ax.grid(alpha=0.2, which="major")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    for ax in axes[-1, :]:
        ax.set_xlabel("Old-intersection total population")
    for ax in axes[:, 0]:
        ax.set_ylabel("Representative-point total population")

    fig.suptitle("Old vs. representative-point total population by year", fontsize=15)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def race_change_totals(summary):
    rows = []
    for race in RACE_COLUMNS:
        rows.append(
            {
                "race": race,
                "label": RACE_LABELS[race],
                "added": numeric_series(summary, f"common_added_{race}").sum(),
                "removed": numeric_series(summary, f"common_removed_{race}").sum(),
                "net": numeric_series(summary, f"common_net_{race}").sum(),
                "old_only": numeric_series(summary, f"old_only_{race}").sum(),
            }
        )
    return pd.DataFrame(rows)


def plot_race_population_changes(summary, output_path):
    totals = race_change_totals(summary)
    y_positions = np.arange(len(totals))
    bar_height = 0.24

    fig, ax = plt.subplots(figsize=(11, 6.4))
    ax.barh(
        y_positions - bar_height,
        totals["added"] / 1_000_000,
        height=bar_height,
        color=MAP_COLORS["added"],
        label="Added by points",
    )
    ax.barh(
        y_positions,
        totals["removed"] / 1_000_000,
        height=bar_height,
        color=MAP_COLORS["removed"],
        label="Removed by points",
    )
    ax.barh(
        y_positions + bar_height,
        totals["net"] / 1_000_000,
        height=bar_height,
        color="#6E7781",
        label="Net change",
    )

    for y_position, row in zip(y_positions, totals.itertuples(index=False)):
        ax.text(
            row.removed / 1_000_000,
            y_position,
            f" {row.removed / 1_000_000:.1f}M",
            va="center",
            fontsize=8,
        )

    ax.axvline(0, color="#2F3437", linewidth=0.9)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(totals["label"])
    ax.invert_yaxis()
    ax.set_title("Aggregate common-pair population change by race", fontsize=14)
    ax.set_xlabel(
        "Population, millions; net is representative-point minus old-intersection"
    )
    ax.legend(frameon=False, loc="lower right")
    ax.text(
        0.01,
        0.03,
        "Added totals are zero for all groups in the current common-pair comparison.",
        transform=ax.transAxes,
        fontsize=9,
        color="#4A4A4A",
    )
    style_distribution_axis(ax)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def race_removed_percentages_by_year(comparison):
    common = race_comparison_frame(comparison)
    rows = []
    for year, year_rows in common.groupby("year"):
        for race in RACE_COLUMNS:
            old_total = year_rows[f"old_{race}"].sum()
            removed = -year_rows[f"{race}_delta"].clip(upper=0).sum()
            rows.append(
                {
                    "year": year,
                    "race": race,
                    "label": RACE_LABELS[race],
                    "old_total": old_total,
                    "removed": removed,
                    "removed_pct": (removed / old_total) * 100
                    if old_total
                    else np.nan,
                }
            )
    return pd.DataFrame(rows)


def plot_race_removed_percentages_by_year(comparison, output_path):
    percentages = race_removed_percentages_by_year(comparison)
    years = sorted(percentages["year"].unique())
    y_positions = np.arange(len(years))
    offsets = np.linspace(-0.34, 0.34, len(RACE_COLUMNS))
    bar_height = 0.1

    fig, ax = plt.subplots(figsize=(12, 7.2))
    for offset, race in zip(offsets, RACE_COLUMNS):
        race_rows = percentages[percentages["race"] == race].set_index("year")
        values = race_rows.reindex(years)["removed_pct"]
        ax.barh(
            y_positions + offset,
            values,
            height=bar_height,
            color=RACE_COLORS[race],
            label=RACE_LABELS[race],
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(years)
    ax.invert_yaxis()
    ax.set_title("Percent of each race group removed by year", fontsize=14)
    ax.set_xlabel(
        "Removed population as percent of old-intersection race population"
    )
    ax.set_ylabel("Tract data year")
    ax.legend(frameon=False, ncol=3, loc="lower right")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, percentages["removed_pct"].max() * 1.15)
    ax.text(
        0.01,
        0.02,
        "`Two or more` has zero old-intersection total before 2000, so those bars are omitted.",
        transform=ax.transAxes,
        fontsize=9,
        color="#4A4A4A",
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def race_comparison_frame(comparison):
    common = comparison[comparison["status"] == "common"].copy()
    for race in RACE_COLUMNS:
        for column in (
            f"old_{race}",
            f"new_{race}",
            f"{race}_delta",
            f"{race}_pct_delta",
        ):
            common[column] = pd.to_numeric(common[column], errors="coerce")
    return common


def plot_race_population_outliers(comparison, output_path, top_n=5):
    common = race_comparison_frame(comparison)
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)

    for ax, race in zip(axes.ravel(), RACE_COLUMNS):
        plot_race_outlier_panel(ax, common, race, top_n)

    fig.suptitle("Largest race-specific population decreases", fontsize=15)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_race_outlier_panel(ax, common, race, top_n):
    delta_column = f"{race}_delta"
    rows = (
        common[common[delta_column] < 0]
        .assign(_removed=lambda frame: -frame[delta_column])
        .sort_values("_removed", ascending=False)
        .head(top_n)
        .iloc[::-1]
    )
    labels = [
        f"{row.year} {row.cbsa_code}\n{short_title(row.cbsa_title)}"
        for row in rows.itertuples(index=False)
    ]
    bars = ax.barh(
        labels,
        rows["_removed"],
        color=RACE_COLORS[race],
        edgecolor="white",
        linewidth=0.35,
    )
    for bar, value in zip(bars, rows["_removed"]):
        ax.text(
            value,
            bar.get_y() + bar.get_height() / 2,
            f" {int(value):,}",
            va="center",
            fontsize=8,
        )

    ax.set_title(RACE_LABELS[race], fontsize=11)
    ax.set_xlabel("Population removed")
    ax.set_xlim(0, rows["_removed"].max() * 1.25)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.xaxis.set_major_formatter(FuncFormatter(compact_axis_label))
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def compact_axis_label(value, _position):
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f}k"
    return f"{value:.0f}"


def short_title(title, max_length=34):
    if len(title) <= max_length:
        return title
    return title[: max_length - 1].rstrip() + "..."


def plot_excluded_overlap_distribution(overlap, output_path):
    area_values = positive_finite_series(overlap, "cbsa_overlap_area_sq_km")
    pct_values = positive_finite_series(overlap, "cbsa_overlap_pct_of_tract")
    area_floor = 1e-6
    pct_floor = 1e-6
    area_plot_values = area_values.clip(lower=area_floor)
    pct_plot_values = pct_values.clip(lower=pct_floor)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    plot_overlap_histogram(
        axes[0],
        area_plot_values,
        log_bins(area_plot_values, area_floor),
        area_values.quantile([0.5, 0.95, 0.99]),
        area_floor,
        "Overlap area",
        "CBSA overlap area, sq km",
        f"{int((area_values < area_floor).sum()):,} values < 1 sq m clipped",
    )
    plot_overlap_histogram(
        axes[1],
        pct_plot_values,
        log_bins(pct_plot_values, pct_floor),
        pct_values.quantile([0.5, 0.95, 0.99]),
        pct_floor,
        "Overlap share of tract",
        "CBSA overlap share of tract area, %",
        f"{int((pct_values < pct_floor).sum()):,} values < 0.000001% clipped",
    )

    fig.suptitle(
        "Excluded tract overlap area distribution\n"
        "Log-scaled x-axes; "
        f"{len(area_values):,} removed-by-points tracts",
        fontsize=13,
    )
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def positive_finite_series(frame, column):
    values = numeric_series(frame, column)
    return values[np.isfinite(values) & (values > 0)]


def log_bins(values, plot_floor):
    return np.logspace(
        np.log10(plot_floor),
        np.ceil(np.log10(values.max())),
        64,
    )


def plot_overlap_histogram(
    ax, values, bins, quantiles, plot_floor, title, xlabel, subtitle
):
    ax.hist(
        values,
        bins=bins,
        color=MAP_COLORS["removed"],
        edgecolor="white",
        linewidth=0.35,
    )
    add_overlap_quantile_lines(ax, quantiles, plot_floor)
    ax.set_xscale("log")
    ax.set_title(f"{title}\n{subtitle}", fontsize=11)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Excluded tract count")
    style_distribution_axis(ax)


def add_overlap_quantile_lines(ax, quantiles, plot_floor):
    labels = {
        0.5: "median",
        0.95: "95th",
        0.99: "99th",
    }
    for quantile, value in quantiles.items():
        line_value = max(value, plot_floor)
        ax.axvline(line_value, color="#2F3437", linewidth=0.8, alpha=0.7)
        ax.text(
            line_value,
            0.96,
            labels.get(quantile, f"{quantile:.0%}"),
            rotation=90,
            ha="right",
            va="top",
            fontsize=8,
            transform=ax.get_xaxis_transform(),
        )


def style_distribution_axis(ax):
    ax.grid(axis="y", alpha=0.25)
    ax.grid(axis="x", alpha=0.12, which="major")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_large_excluded_overlap_examples(comparison, output_path, defs_root):
    examples = [
        read_large_excluded_overlap_example(comparison, case, defs_root)
        for case in LARGE_EXCLUDED_OVERLAP_EXAMPLES
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.3), constrained_layout=True)
    for ax, example in zip(axes, examples):
        plot_large_overlap_example_layer(ax, example)

    handles = [
        Patch(
            facecolor=MAP_COLORS["retained"],
            edgecolor=MAP_COLORS["retained_edge"],
            label="Retained by points",
        ),
        Patch(
            facecolor=MAP_COLORS["removed"],
            edgecolor=MAP_COLORS["removed_edge"],
            alpha=0.3,
            label="Selected excluded tract",
        ),
        Patch(
            facecolor=MAP_COLORS["removed"],
            edgecolor=MAP_COLORS["removed_edge"],
            hatch="///",
            label="Overlap with CBSA",
        ),
        Patch(
            facecolor="none",
            edgecolor=MAP_COLORS["outline"],
            label="March 2020 CBSA outline",
        ),
        Line2D(
            [0],
            [0],
            marker="x",
            color=MAP_COLORS["outline"],
            linestyle="none",
            markersize=7,
            label="Representative point",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=5,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
    )
    fig.suptitle(
        "Large 1980 excluded overlaps under representative-point assignment",
        fontsize=14,
    )
    fig.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(fig)
    return output_path


def read_large_excluded_overlap_example(comparison, case, defs_root):
    year = case["year"]
    cbsa_code = case["cbsa_code"]
    vintage = case["vintage"]
    tract_id = case["tract_id"]

    outline = read_definition_outline(comparison, cbsa_code, vintage, (year,), defs_root)
    layer = read_difference_layers(
        comparison, cbsa_code, vintage, year, target_crs=outline.crs
    )
    selected = layer["removed"][layer["removed"]["_plot_id"] == tract_id].copy()
    if selected.empty:
        raise ValueError(
            f"Could not find removed tract {tract_id} for {cbsa_code} {year}"
        )

    outline_geometry = union_geometry(outline)
    overlap_parts = polygon_parts(selected.geometry.iloc[0].intersection(outline_geometry))
    overlap = gpd.GeoDataFrame(geometry=overlap_parts, crs=selected.crs)
    representative_point = gpd.GeoDataFrame(
        geometry=selected.geometry.representative_point(), crs=selected.crs
    )
    overlap_area = float(overlap.geometry.area.sum())
    tract_area = float(selected.geometry.area.iloc[0])
    bounds = shared_bounds(outline, selected)
    bounds = padded_bounds(bounds, padding_ratio=0.06, min_padding=2500)

    row = find_map_row(comparison, cbsa_code, vintage, year)
    return {
        "year": year,
        "cbsa_code": cbsa_code,
        "cbsa_title": row["cbsa_title"],
        "tract_id": tract_id,
        "retained": layer["retained"],
        "selected": selected,
        "overlap": overlap,
        "outline": outline,
        "representative_point": representative_point,
        "overlap_sq_km": overlap_area / 1_000_000,
        "overlap_pct": overlap_area / tract_area * 100,
        "bounds": bounds,
    }


def plot_large_overlap_example_layer(ax, example):
    example["retained"].plot(
        ax=ax,
        color=MAP_COLORS["retained"],
        edgecolor=MAP_COLORS["retained_edge"],
        linewidth=0.12,
        alpha=0.9,
        zorder=1,
    )
    example["selected"].plot(
        ax=ax,
        color=MAP_COLORS["removed"],
        edgecolor=MAP_COLORS["removed_edge"],
        linewidth=0.8,
        alpha=0.3,
        zorder=2,
    )
    if not example["overlap"].empty:
        example["overlap"].plot(
            ax=ax,
            color=MAP_COLORS["removed"],
            edgecolor=MAP_COLORS["removed_edge"],
            linewidth=0.7,
            hatch="///",
            alpha=0.95,
            zorder=3,
        )
    example["outline"].boundary.plot(
        ax=ax,
        color=MAP_COLORS["outline"],
        linewidth=1.45,
        alpha=0.95,
        zorder=4,
    )
    example["representative_point"].plot(
        ax=ax,
        marker="x",
        color=MAP_COLORS["outline"],
        markersize=44,
        linewidth=1.5,
        zorder=5,
    )

    apply_map_axes(ax, example["bounds"])
    ax.set_title(
        f"{example['cbsa_title']}\n"
        f"{example['tract_id']}: {example['overlap_sq_km']:,.1f} sq km "
        f"({example['overlap_pct']:.1f}%)",
        fontsize=10,
    )


def plot_chicago_difference_tiles(
    comparison, figure_root, cbsa_code, vintage, years, defs_root
):
    outline = read_definition_outline(comparison, cbsa_code, vintage, years, defs_root)
    layers = [
        read_difference_layers(
            comparison, cbsa_code, vintage, year, target_crs=outline.crs
        )
        for year in years
    ]
    bounds = shared_bounds(
        outline,
        *[layer["old_frame"] for layer in layers],
        *[layer["new_frame"] for layer in layers],
    )
    output_path = (
        figure_root
        / f"chicago_{cbsa_code}_{vintage}_assignment_differences_by_year.png"
    )

    fig, axes = plt.subplots(2, 3, figsize=(12, 12), constrained_layout=True)
    for ax, layer in zip(axes.ravel(), layers):
        plot_difference_layer(ax, layer, outline, bounds)

    handles = [
        Patch(
            facecolor="none",
            edgecolor=MAP_COLORS["outline"],
            label="March 2020 CBSA outline",
        ),
        Patch(
            facecolor=MAP_COLORS["retained"],
            edgecolor=MAP_COLORS["retained_edge"],
            label="Retained",
        ),
        Patch(
            facecolor=MAP_COLORS["removed"],
            edgecolor=MAP_COLORS["removed_edge"],
            label="Removed by points",
        ),
        Patch(
            facecolor=MAP_COLORS["added"],
            edgecolor=MAP_COLORS["added_edge"],
            label="Added by points",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, -0.01),
    )
    fig.suptitle(
        f"Chicago tract assignment differences ({cbsa_code}, {display_vintage(vintage)})",
        fontsize=15,
    )
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def read_difference_layers(comparison, cbsa_code, vintage, year, target_crs=None):
    row = find_map_row(comparison, cbsa_code, vintage, year)
    old_frame, new_frame = read_map_frames(row)
    old_frame, new_frame = align_crs(old_frame, new_frame, target_crs=target_crs)
    old_ids, new_ids, id_column = tract_id_sets(old_frame, new_frame)
    old_with_ids = with_plot_id(old_frame, id_column)
    new_with_ids = with_plot_id(new_frame, id_column)

    return {
        "year": str(year),
        "old_frame": old_frame,
        "new_frame": new_frame,
        "retained": old_with_ids[old_with_ids["_plot_id"].isin(old_ids & new_ids)],
        "removed": old_with_ids[old_with_ids["_plot_id"].isin(old_ids - new_ids)],
        "added": new_with_ids[new_with_ids["_plot_id"].isin(new_ids - old_ids)],
    }


def plot_difference_layer(ax, layer, outline, bounds):
    retained = layer["retained"]
    removed = layer["removed"]
    added = layer["added"]

    retained.plot(
        ax=ax,
        color=MAP_COLORS["retained"],
        edgecolor=MAP_COLORS["retained_edge"],
        linewidth=0.02,
        alpha=0.9,
        zorder=1,
    )
    if not removed.empty:
        removed.plot(
            ax=ax,
            color=MAP_COLORS["removed"],
            edgecolor=MAP_COLORS["removed_edge"],
            linewidth=0.08,
            zorder=2,
        )
    if not added.empty:
        added.plot(
            ax=ax,
            color=MAP_COLORS["added"],
            edgecolor=MAP_COLORS["added_edge"],
            linewidth=0.08,
            zorder=3,
        )
    outline.boundary.plot(
        ax=ax,
        color=MAP_COLORS["outline"],
        linewidth=1.25,
        alpha=0.95,
        zorder=4,
    )

    apply_map_axes(ax, bounds)
    ax.set_title(
        f"{layer['year']}\n"
        f"{len(retained):,} retained, {len(removed):,} removed, {len(added):,} added",
        fontsize=10,
    )


def plot_chicago_positive_overlap_example(
    comparison, figure_root, cbsa_code, vintage, defs_root, year="1970"
):
    outline = read_definition_outline(comparison, cbsa_code, vintage, (year,), defs_root)
    layer = read_difference_layers(
        comparison, cbsa_code, vintage, year, target_crs=outline.crs
    )
    outline_geometry = union_geometry(outline)
    example, overlap, total_overlap_area = select_positive_overlap_example(
        layer["removed"], outline_geometry
    )
    representative_point = gpd.GeoDataFrame(
        geometry=example.geometry.representative_point(), crs=example.crs
    )

    tract_id = example["_plot_id"].iloc[0]
    county = first_available_value(example, ("COUNTY_df", "COUNTY", "COUNTYNH"))
    state = first_available_value(example, ("STATE", "STATENH"))
    tract_name = first_available_value(example, ("NAME", "NAMELSAD", "TRACTA"))
    overlap_sq_km = float(total_overlap_area / 1_000_000)
    overlap_pct = float(total_overlap_area / example.geometry.area.iloc[0] * 100)

    output_path = (
        figure_root
        / f"chicago_{cbsa_code}_{vintage}_{year}_positive_overlap_example.png"
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), constrained_layout=True)
    plot_positive_overlap_context(
        axes[0],
        layer["retained"],
        example,
        outline,
        representative_point,
        padded_bounds(example.total_bounds, padding_ratio=0.08, min_padding=3500),
    )
    axes[0].set_title(
        f"{year} excluded tract context\n{county}, {state}, {tract_name}",
        fontsize=10,
    )

    plot_positive_overlap_zoom(
        axes[1],
        layer["retained"],
        example,
        overlap,
        outline,
        padded_bounds(overlap.total_bounds, padding_ratio=0.25, min_padding=900),
    )
    axes[1].set_title("Zoom on largest positive area overlap", fontsize=10)

    handles = [
        Patch(
            facecolor=MAP_COLORS["retained"],
            edgecolor=MAP_COLORS["retained_edge"],
            label="Retained",
        ),
        Patch(
            facecolor=MAP_COLORS["removed"],
            edgecolor=MAP_COLORS["removed_edge"],
            label="Removed by points",
        ),
        Patch(
            facecolor=MAP_COLORS["removed"],
            edgecolor=MAP_COLORS["removed_edge"],
            hatch="///",
            label="Positive overlap",
        ),
        Patch(
            facecolor="none",
            edgecolor=MAP_COLORS["outline"],
            label="March 2020 CBSA outline",
        ),
        Line2D(
            [0],
            [0],
            marker="x",
            color=MAP_COLORS["outline"],
            linestyle="none",
            markersize=6,
            label="Representative point",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=5,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
    )
    fig.suptitle(
        f"Chicago 1970 tract with positive CBSA overlap but excluded by representative point\n"
        f"{tract_id}: overlap {overlap_sq_km:.3f} sq km ({overlap_pct:.3f}% of tract)",
        fontsize=13,
    )
    fig.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(fig)
    return output_path


def select_positive_overlap_example(removed, outline_geometry):
    if removed.empty:
        raise ValueError("Expected at least one removed tract")

    candidates = []
    for index, row in removed.iterrows():
        overlap_parts = polygon_parts(row.geometry.intersection(outline_geometry))
        if not overlap_parts:
            continue
        total_area = sum(part.area for part in overlap_parts)
        if total_area <= 0:
            continue
        largest_part = max(overlap_parts, key=lambda part: part.area)
        candidates.append((total_area, index, largest_part))

    if not candidates:
        raise ValueError("No removed tract has a positive area overlap")

    total_area, index, overlap_geometry = max(
        candidates, key=lambda candidate: candidate[0]
    )
    example = removed.loc[[index]].copy()
    overlap = gpd.GeoDataFrame(
        {"_plot_id": example["_plot_id"].to_numpy()},
        geometry=[overlap_geometry],
        crs=removed.crs,
    )
    return example, overlap, total_area


def plot_positive_overlap_context(
    ax, retained, example, outline, representative_point, bounds
):
    retained.plot(
        ax=ax,
        color=MAP_COLORS["retained"],
        edgecolor=MAP_COLORS["retained_edge"],
        linewidth=0.12,
        alpha=0.9,
        zorder=1,
    )
    example.plot(
        ax=ax,
        color=MAP_COLORS["removed"],
        edgecolor=MAP_COLORS["removed_edge"],
        linewidth=1.0,
        alpha=0.92,
        zorder=2,
    )
    outline.boundary.plot(
        ax=ax,
        color=MAP_COLORS["outline"],
        linewidth=1.4,
        zorder=3,
    )
    representative_point.plot(
        ax=ax,
        marker="x",
        color=MAP_COLORS["outline"],
        markersize=36,
        linewidth=1.4,
        zorder=4,
    )
    apply_map_axes(ax, bounds)


def plot_positive_overlap_zoom(ax, retained, example, overlap, outline, bounds):
    retained.plot(
        ax=ax,
        color=MAP_COLORS["retained"],
        edgecolor=MAP_COLORS["retained_edge"],
        linewidth=0.16,
        alpha=0.9,
        zorder=1,
    )
    example.plot(
        ax=ax,
        color=MAP_COLORS["removed"],
        edgecolor=MAP_COLORS["removed_edge"],
        linewidth=0.8,
        alpha=0.25,
        zorder=2,
    )
    overlap.plot(
        ax=ax,
        color=MAP_COLORS["removed"],
        edgecolor=MAP_COLORS["removed_edge"],
        linewidth=1.0,
        hatch="///",
        alpha=0.95,
        zorder=3,
    )
    outline.boundary.plot(
        ax=ax,
        color=MAP_COLORS["outline"],
        linewidth=1.8,
        zorder=4,
    )
    apply_map_axes(ax, bounds)


def first_available_value(frame, columns):
    for column in columns:
        if column in frame.columns:
            value = frame[column].iloc[0]
            if pd.notna(value):
                return str(value).strip()
    return "unknown"


def find_map_row(comparison, cbsa_code, vintage, year):
    matches = comparison[
        (comparison["year"] == str(year))
        & (comparison["cbsa_code"] == str(cbsa_code))
        & (comparison["vintage"] == vintage)
        & (comparison["status"] == "common")
    ]
    if matches.empty:
        raise ValueError(
            f"No common row found for year={year}, cbsa_code={cbsa_code}, vintage={vintage}"
        )
    return matches.iloc[0]


def display_vintage(vintage):
    return vintage.replace("_", " ").title()


def read_definition_outline(comparison, cbsa_code, vintage, years, defs_root):
    row = find_first_map_row(comparison, cbsa_code, vintage, years)
    path = defs_root / f"{row['stem']}.shp"
    if not path.exists():
        raise FileNotFoundError(f"Definition shapefile not found: {path}")
    return gpd.read_file(path)


def find_first_map_row(comparison, cbsa_code, vintage, years):
    for year in years:
        matches = comparison[
            (comparison["year"] == str(year))
            & (comparison["cbsa_code"] == str(cbsa_code))
            & (comparison["vintage"] == vintage)
            & (comparison["status"] == "common")
        ]
        if not matches.empty:
            return matches.iloc[0]
    raise ValueError(
        f"No common rows found for cbsa_code={cbsa_code}, vintage={vintage}"
    )


def read_map_frames(row):
    old_path = Path(row["old_path"])
    new_path = Path(row["new_path"])
    return gpd.read_file(old_path), gpd.read_file(new_path)


def align_crs(old_frame, new_frame, target_crs=None):
    if target_crs is not None:
        if old_frame.crs and old_frame.crs != target_crs:
            old_frame = old_frame.to_crs(target_crs)
        if new_frame.crs and new_frame.crs != target_crs:
            new_frame = new_frame.to_crs(target_crs)
    elif old_frame.crs and new_frame.crs and old_frame.crs != new_frame.crs:
        new_frame = new_frame.to_crs(old_frame.crs)
    return old_frame, new_frame


def tract_id_sets(old_frame, new_frame):
    for column in ID_COLUMNS:
        if column in old_frame.columns and column in new_frame.columns:
            return (
                set(clean_ids(old_frame[column])),
                set(clean_ids(new_frame[column])),
                column,
            )
    raise ValueError("Expected a tract identifier column in both Chicago shapefiles")


def with_plot_id(frame, id_column):
    frame = frame.copy()
    frame["_plot_id"] = clean_ids(frame[id_column])
    return frame


def clean_ids(series):
    return series.astype(str).str.strip()


def union_geometry(frame):
    geometry = frame.geometry
    if hasattr(geometry, "union_all"):
        return geometry.union_all()
    return geometry.unary_union


def polygon_parts(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)
    if hasattr(geometry, "geoms"):
        parts = []
        for part in geometry.geoms:
            parts.extend(polygon_parts(part))
        return parts
    return []


def shared_bounds(*frames):
    all_bounds = np.array([frame.total_bounds for frame in frames])
    xmin = float(all_bounds[:, 0].min())
    ymin = float(all_bounds[:, 1].min())
    xmax = float(all_bounds[:, 2].max())
    ymax = float(all_bounds[:, 3].max())
    padding = max(xmax - xmin, ymax - ymin) * 0.02
    return xmin - padding, ymin - padding, xmax + padding, ymax + padding


def apply_map_axes(ax, bounds):
    xmin, ymin, xmax, ymax = bounds
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")
    ax.axis("off")


def padded_bounds(bounds, padding_ratio=0.15, min_padding=0):
    xmin, ymin, xmax, ymax = bounds
    width = xmax - xmin
    height = ymax - ymin
    padding = max(width, height) * padding_ratio
    padding = max(padding, min_padding)
    return xmin - padding, ymin - padding, xmax + padding, ymax + padding


if __name__ == "__main__":
    main()
