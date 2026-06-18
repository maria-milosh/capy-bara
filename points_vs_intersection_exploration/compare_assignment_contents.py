import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import geopandas as gpd
import pandas as pd


YEARS = ("1970", "1980", "1990", "2000", "2010", "2020")
DEFAULT_VINTAGE = "march_2020"
NEW_ROOT = Path("cbsas")
OLD_ROOT = Path("old_cbsas")
DEFS_ROOT = Path("cbsas/defs")
OUT_ROOT = Path("points_vs_intersection_exploration")

ID_COLUMNS = ("GISJOIN", "GEOID", "NHGISCODE")
RACE_COLUMNS = ("WHITE", "BLACK", "AMIN", "ASIAN", "2MORE", "POC")
POPULATION_COLUMNS = ("TOTPOP",) + RACE_COLUMNS
TRACT_DETAIL_COLUMNS = (
    "GISJOIN",
    "GEOID",
    "NHGISCODE",
    "YEAR",
    "STATE",
    "STATEFP",
    "STATEFP_df",
    "STATENH",
    "COUNTY",
    "COUNTYFP",
    "COUNTYFP_d",
    "COUNTYNH",
    "TRACTA",
    "TRACTCE",
    "NAME",
    "NAME_df",
    "NAMELSAD",
    "ALAND",
    "AWATER",
    "INTPTLAT",
    "INTPTLON",
)
GRAPH_STAT_FIELDS = (
    "nodes",
    "edges",
    "components",
    "largest_component_nodes",
    "largest_component_share",
    "isolates",
    "average_degree",
    "edge_density",
    "zero_population_nodes",
    "total_population",
)
GRAPH_ASSIGNMENT_FIELDS = (
    "old_orig_nodes",
    "new_orig_nodes",
    "orig_nodes_delta",
    "old_orig_edges",
    "new_orig_edges",
    "orig_edges_delta",
    "old_orig_components",
    "new_orig_components",
    "orig_components_delta",
    "old_orig_isolates",
    "new_orig_isolates",
    "orig_isolates_delta",
    "old_connected_nodes",
    "new_connected_nodes",
    "connected_nodes_delta",
    "old_connected_edges",
    "new_connected_edges",
    "connected_edges_delta",
    "old_nodes_contracted",
    "new_nodes_contracted",
    "nodes_contracted_delta",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Compare March 2020 CBSA tract assignments from representative "
            "points against old any-intersection assignments."
        )
    )
    parser.add_argument("--old-root", type=Path, default=OLD_ROOT)
    parser.add_argument("--new-root", type=Path, default=NEW_ROOT)
    parser.add_argument("--defs-root", type=Path, default=DEFS_ROOT)
    parser.add_argument("--out-root", type=Path, default=OUT_ROOT)
    parser.add_argument("--vintage", default=DEFAULT_VINTAGE)
    parser.add_argument("--years", nargs="*", default=YEARS)
    parser.add_argument("--top-n", type=int, default=25)
    parser.add_argument("--min-tracts-for-pct", type=int, default=5)
    parser.add_argument("--min-population-for-pct", type=int, default=10000)
    return parser.parse_args()


def output_stem(path):
    suffix = "_cbsa_tracts"
    if path.stem.endswith(suffix):
        return path.stem[: -len(suffix)]
    return path.stem


def vintage_from_stem(stem):
    parts = stem.split("_", 2)
    if len(parts) < 3:
        return ""
    return parts[2]


def read_def_metadata(defs_root):
    metadata = {}
    for path in defs_root.glob("*.json"):
        with path.open() as f:
            payload = json.load(f)
        if isinstance(payload, str):
            payload = json.loads(payload)
        metadata[path.stem] = payload
    return metadata


def read_outputs(root, years, vintage):
    outputs = defaultdict(dict)
    pattern = f"*_{vintage}_cbsa_tracts.shp"
    for year in years:
        for path in sorted((root / year).glob(pattern)):
            stem = output_stem(path)
            if vintage_from_stem(stem) == vintage:
                outputs[year][stem] = path
    return outputs


def metadata_row(year, stem, status, old_path, new_path, metadata):
    info = metadata.get(stem, {})
    parts = stem.split("_", 2)
    filename_population = parts[0] if len(parts) > 0 else ""
    cbsa_code = parts[1] if len(parts) > 1 else info.get("cbsa_code", "")
    vintage = parts[2] if len(parts) > 2 else ""
    return {
        "year": year,
        "status": status,
        "stem": stem,
        "cbsa_code": info.get("cbsa_code", cbsa_code),
        "cbsa_title": info.get("cbsa_title", ""),
        "vintage": vintage,
        "filename_population": filename_population,
        "definition_population": info.get("total_population", ""),
        "component_counties_count": len(info.get("component_counties_fips", [])),
        "old_path": str(old_path) if old_path else "",
        "new_path": str(new_path) if new_path else "",
    }


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: blank_if_none(row.get(field)) for field in fieldnames})


def blank_if_none(value):
    if value is None:
        return ""
    return value


def clean_value(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def numeric_value(value):
    if value is None or pd.isna(value):
        return None
    converted = pd.to_numeric(value, errors="coerce")
    if pd.isna(converted):
        return None
    return float(converted)


def sum_column(frame, column):
    if frame is None or column not in frame.columns:
        return None
    values = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    return int(values.sum())


def population_totals(frame):
    return {column: sum_column(frame, column) for column in POPULATION_COLUMNS}


def pct_delta(new_value, old_value):
    if old_value in ("", None) or new_value in ("", None):
        return ""
    if old_value == 0:
        return ""
    return round(((new_value - old_value) / old_value) * 100, 6)


def delta(new_value, old_value):
    if old_value in ("", None) or new_value in ("", None):
        return ""
    return new_value - old_value


def read_frame(path):
    if path is None:
        return None
    return gpd.read_file(path, ignore_geometry=True)


def tract_id_column(frame, path):
    for column in ID_COLUMNS:
        if column in frame.columns:
            return column
    for column in frame.columns:
        if column.startswith("GJOIN"):
            return column
    raise ValueError(f"No tract identifier column found in {path}")


def rows_by_tract_id(frame, path):
    column = tract_id_column(frame, path)
    rows = {}
    duplicate_count = 0
    for _, record in frame.iterrows():
        tract_id = clean_value(record[column])
        if not tract_id:
            continue
        if tract_id in rows:
            duplicate_count += 1
            continue
        rows[tract_id] = record
    return column, rows, duplicate_count


def membership_change_row(base, change_type, source_path, id_column, tract_id, record):
    row = {
        "year": base["year"],
        "stem": base["stem"],
        "cbsa_code": base["cbsa_code"],
        "cbsa_title": base["cbsa_title"],
        "vintage": base["vintage"],
        "change_type": change_type,
        "source_path": str(source_path),
        "tract_id_column": id_column,
        "tract_id": tract_id,
    }
    for column in POPULATION_COLUMNS:
        row[column] = record_value(record, column)
    for column in TRACT_DETAIL_COLUMNS:
        row[column] = record_value(record, column)
    return row


def record_value(record, column):
    if column not in record.index:
        return ""
    value = record[column]
    if pd.isna(value):
        return ""
    return value


def graph_paths(shp_path, stem):
    if shp_path is None:
        return None, None
    base = f"{stem}_cbsa_tracts"
    return (
        shp_path.with_name(f"{base}_orig.json"),
        shp_path.with_name(f"{base}_connected.json"),
    )


def read_log_counts(path):
    counts = Counter()
    if not path.exists():
        return counts
    with path.open() as f:
        for row in csv.DictReader(f):
            counts[row["filename"]] += 1
    return counts


def graph_stats(path):
    if path is None or not path.exists():
        return empty_graph_stats()

    with path.open() as f:
        payload = json.load(f)

    nodes = payload.get("nodes", [])
    adjacency = payload.get("adjacency", [])
    node_ids = [node.get("id", idx) for idx, node in enumerate(nodes)]
    neighbors_by_id = {node_id: set() for node_id in node_ids}
    edges = set()

    for idx, neighbors in enumerate(adjacency):
        if idx >= len(node_ids):
            continue
        source = node_ids[idx]
        neighbors_by_id.setdefault(source, set())
        for neighbor in neighbors:
            target = neighbor.get("id")
            if target is None:
                continue
            neighbors_by_id.setdefault(target, set())
            neighbors_by_id[source].add(target)
            neighbors_by_id[target].add(source)
            edges.add(edge_key(source, target))

    node_count = len(neighbors_by_id)
    edge_count = len(edges)
    component_sizes = connected_component_sizes(neighbors_by_id)
    largest_component_nodes = max(component_sizes) if component_sizes else 0
    isolates = sum(1 for neighbors in neighbors_by_id.values() if len(neighbors) == 0)
    total_population = sum_graph_population(nodes)

    return {
        "nodes": node_count,
        "edges": edge_count,
        "components": len(component_sizes),
        "largest_component_nodes": largest_component_nodes,
        "largest_component_share": round(largest_component_nodes / node_count, 6)
        if node_count
        else 0,
        "isolates": isolates,
        "average_degree": round((2 * edge_count) / node_count, 6)
        if node_count
        else 0,
        "edge_density": round((2 * edge_count) / (node_count * (node_count - 1)), 8)
        if node_count > 1
        else 0,
        "zero_population_nodes": sum_zero_population_nodes(nodes),
        "total_population": total_population,
    }


def empty_graph_stats():
    return {field: "" for field in GRAPH_STAT_FIELDS}


def edge_key(source, target):
    if repr(source) <= repr(target):
        return (repr(source), repr(target))
    return (repr(target), repr(source))


def connected_component_sizes(neighbors_by_id):
    unseen = set(neighbors_by_id)
    sizes = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        size = 1
        while stack:
            node = stack.pop()
            for neighbor in neighbors_by_id[node]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
                    size += 1
        sizes.append(size)
    return sizes


def sum_graph_population(nodes):
    total = 0
    found = False
    for node in nodes:
        value = numeric_value(node.get("TOTPOP"))
        if value is not None:
            found = True
            total += value
    if not found:
        return ""
    return int(total)


def sum_zero_population_nodes(nodes):
    count = 0
    found = False
    for node in nodes:
        value = numeric_value(node.get("TOTPOP"))
        if value is None:
            continue
        found = True
        if value == 0:
            count += 1
    if not found:
        return ""
    return count


def add_graph_stats(row, side, stage, stats):
    for field in GRAPH_STAT_FIELDS:
        row[f"{side}_{stage}_{field}"] = stats[field]


def graph_structure_row(base, stem, old_path, new_path, island_counts, overlap_counts):
    row = dict(base)
    old_orig_path, old_connected_path = graph_paths(old_path, stem)
    new_orig_path, new_connected_path = graph_paths(new_path, stem)

    row.update(
        {
            "old_orig_path": str(old_orig_path) if old_orig_path else "",
            "old_connected_path": str(old_connected_path) if old_connected_path else "",
            "new_orig_path": str(new_orig_path) if new_orig_path else "",
            "new_connected_path": str(new_connected_path) if new_connected_path else "",
            "old_island_log_rows": island_counts[str(old_path)] if old_path else "",
            "new_island_log_rows": island_counts[str(new_path)] if new_path else "",
            "old_large_populated_overlap_rows": overlap_counts[str(old_path)]
            if old_path
            else "",
            "new_large_populated_overlap_rows": overlap_counts[str(new_path)]
            if new_path
            else "",
        }
    )

    old_orig = graph_stats(old_orig_path)
    old_connected = graph_stats(old_connected_path)
    new_orig = graph_stats(new_orig_path)
    new_connected = graph_stats(new_connected_path)

    add_graph_stats(row, "old", "orig", old_orig)
    add_graph_stats(row, "old", "connected", old_connected)
    add_graph_stats(row, "new", "orig", new_orig)
    add_graph_stats(row, "new", "connected", new_connected)

    for field in GRAPH_STAT_FIELDS:
        row[f"orig_{field}_delta"] = delta(new_orig[field], old_orig[field])
        row[f"connected_{field}_delta"] = delta(
            new_connected[field], old_connected[field]
        )

    row["old_nodes_contracted"] = delta(
        old_orig["nodes"], old_connected["nodes"]
    )
    row["new_nodes_contracted"] = delta(
        new_orig["nodes"], new_connected["nodes"]
    )
    row["nodes_contracted_delta"] = delta(
        row["new_nodes_contracted"], row["old_nodes_contracted"]
    )
    row["old_edges_changed_from_orig_to_connected"] = delta(
        old_connected["edges"], old_orig["edges"]
    )
    row["new_edges_changed_from_orig_to_connected"] = delta(
        new_connected["edges"], new_orig["edges"]
    )
    row["edges_changed_from_orig_to_connected_delta"] = delta(
        row["new_edges_changed_from_orig_to_connected"],
        row["old_edges_changed_from_orig_to_connected"],
    )
    row["old_population_changed_from_orig_to_connected"] = delta(
        old_connected["total_population"], old_orig["total_population"]
    )
    row["new_population_changed_from_orig_to_connected"] = delta(
        new_connected["total_population"], new_orig["total_population"]
    )
    row["population_changed_from_orig_to_connected_delta"] = delta(
        row["new_population_changed_from_orig_to_connected"],
        row["old_population_changed_from_orig_to_connected"],
    )
    return row


def comparison_row(base, old_frame, new_frame, old_path, new_path, graph_row):
    row = dict(base)
    old_totals = population_totals(old_frame)
    new_totals = population_totals(new_frame)

    row["old_tract_count"] = len(old_frame) if old_frame is not None else ""
    row["new_tract_count"] = len(new_frame) if new_frame is not None else ""
    row["tract_count_delta"] = delta(row["new_tract_count"], row["old_tract_count"])
    row["tract_count_pct_delta"] = pct_delta(
        row["new_tract_count"], row["old_tract_count"]
    )

    old_id_column, old_rows, old_duplicate_count = id_info(old_frame, old_path)
    new_id_column, new_rows, new_duplicate_count = id_info(new_frame, new_path)
    row["old_duplicate_tract_id_count"] = old_duplicate_count
    row["new_duplicate_tract_id_count"] = new_duplicate_count

    if old_frame is not None and new_frame is not None:
        old_ids = set(old_rows)
        new_ids = set(new_rows)
        row["retained_tract_count"] = len(old_ids & new_ids)
        row["removed_tract_count"] = len(old_ids - new_ids)
        row["added_tract_count"] = len(new_ids - old_ids)
    else:
        row["retained_tract_count"] = ""
        row["removed_tract_count"] = ""
        row["added_tract_count"] = ""

    row["old_total_population"] = old_totals["TOTPOP"]
    row["new_total_population"] = new_totals["TOTPOP"]
    row["population_delta"] = delta(
        row["new_total_population"], row["old_total_population"]
    )
    row["population_pct_delta"] = pct_delta(
        row["new_total_population"], row["old_total_population"]
    )

    for column in RACE_COLUMNS:
        row[f"old_{column}"] = old_totals[column]
        row[f"new_{column}"] = new_totals[column]
        row[f"{column}_delta"] = delta(new_totals[column], old_totals[column])
        row[f"{column}_pct_delta"] = pct_delta(
            new_totals[column], old_totals[column]
        )

    for field in GRAPH_ASSIGNMENT_FIELDS:
        row[field] = graph_row.get(field, "")

    return row, old_id_column, old_rows, new_id_column, new_rows


def id_info(frame, path):
    if frame is None:
        return "", {}, ""
    return rows_by_tract_id(frame, path)


def add_membership_rows(
    membership_rows,
    base,
    old_path,
    new_path,
    old_id_column,
    old_rows,
    new_id_column,
    new_rows,
):
    old_ids = set(old_rows)
    new_ids = set(new_rows)
    for tract_id in sorted(old_ids - new_ids):
        membership_rows.append(
            membership_change_row(
                base,
                "removed_by_points",
                old_path,
                old_id_column,
                tract_id,
                old_rows[tract_id],
            )
        )
    for tract_id in sorted(new_ids - old_ids):
        membership_rows.append(
            membership_change_row(
                base,
                "added_by_points",
                new_path,
                new_id_column,
                tract_id,
                new_rows[tract_id],
            )
        )


def summary_rows(comparison_rows, membership_rows, years):
    rows_by_year = defaultdict(list)
    membership_by_year = defaultdict(list)
    for row in comparison_rows:
        rows_by_year[row["year"]].append(row)
    for row in membership_rows:
        membership_by_year[row["year"]].append(row)

    summary = []
    for year in years:
        rows = rows_by_year[year]
        old_rows = [row for row in rows if row["old_path"]]
        new_rows = [row for row in rows if row["new_path"]]
        common_rows = [row for row in rows if row["status"] == "common"]
        old_only_rows = [row for row in rows if row["status"] == "old_only"]
        new_only_rows = [row for row in rows if row["status"] == "new_only"]

        row = {
            "year": year,
            "old_intersection_shp_count": len(old_rows),
            "new_points_shp_count": len(new_rows),
            "common_count": len(common_rows),
            "old_only_count": len(old_only_rows),
            "new_only_count": len(new_only_rows),
            "old_unique_cbsa_count": unique_count(old_rows, "cbsa_code"),
            "new_unique_cbsa_count": unique_count(new_rows, "cbsa_code"),
            "common_unique_cbsa_count": unique_count(common_rows, "cbsa_code"),
            "old_only_unique_cbsa_count": unique_count(old_only_rows, "cbsa_code"),
            "new_only_unique_cbsa_count": unique_count(new_only_rows, "cbsa_code"),
            "common_no_tract_change_count": count_where(
                common_rows, "tract_count_delta", 0
            ),
            "common_fewer_tracts_count": count_signed(
                common_rows, "tract_count_delta", negative=True
            ),
            "common_more_tracts_count": count_signed(
                common_rows, "tract_count_delta", negative=False
            ),
            "common_population_decrease_count": count_signed(
                common_rows, "population_delta", negative=True
            ),
            "common_population_increase_count": count_signed(
                common_rows, "population_delta", negative=False
            ),
            "common_orig_components_changed_count": count_nonzero(
                common_rows, "orig_components_delta"
            ),
            "common_connected_nodes_changed_count": count_nonzero(
                common_rows, "connected_nodes_delta"
            ),
            "common_connected_edges_changed_count": count_nonzero(
                common_rows, "connected_edges_delta"
            ),
        }
        row.update(prefixed_stats("old_tract_count", old_rows, "old_tract_count"))
        row.update(prefixed_stats("new_tract_count", new_rows, "new_tract_count"))
        row.update(
            prefixed_stats(
                "old_total_population", old_rows, "old_total_population"
            )
        )
        row.update(
            prefixed_stats(
                "new_total_population", new_rows, "new_total_population"
            )
        )
        row.update(
            prefixed_stats(
                "old_connected_nodes", old_rows, "old_connected_nodes"
            )
        )
        row.update(
            prefixed_stats(
                "new_connected_nodes", new_rows, "new_connected_nodes"
            )
        )
        row.update(
            prefixed_stats(
                "old_connected_edges", old_rows, "old_connected_edges"
            )
        )
        row.update(
            prefixed_stats(
                "new_connected_edges", new_rows, "new_connected_edges"
            )
        )

        year_membership = membership_by_year[year]
        for column in POPULATION_COLUMNS:
            added = sum_membership(year_membership, "added_by_points", column)
            removed = sum_membership(year_membership, "removed_by_points", column)
            row[f"common_added_{column}"] = added
            row[f"common_removed_{column}"] = removed
            row[f"common_net_{column}"] = added - removed
            row[f"old_only_{column}"] = sum_row_values(
                old_only_rows, f"old_{column}" if column != "TOTPOP" else "old_total_population"
            )
            row[f"new_only_{column}"] = sum_row_values(
                new_only_rows, f"new_{column}" if column != "TOTPOP" else "new_total_population"
            )

        summary.append(row)
    return summary


def unique_count(rows, field):
    return len({row[field] for row in rows if row.get(field)})


def count_where(rows, field, value):
    return sum(1 for row in rows if row.get(field) == value)


def count_nonzero(rows, field):
    return sum(1 for row in rows if row.get(field) not in ("", None, 0))


def count_signed(rows, field, negative):
    count = 0
    for row in rows:
        value = row.get(field)
        if value in ("", None, 0):
            continue
        if negative and value < 0:
            count += 1
        if not negative and value > 0:
            count += 1
    return count


def prefixed_stats(prefix, rows, field):
    values = [row[field] for row in rows if row.get(field) not in ("", None)]
    if not values:
        return {
            f"{prefix}_mean": "",
            f"{prefix}_median": "",
            f"{prefix}_min": "",
            f"{prefix}_max": "",
        }
    return {
        f"{prefix}_mean": round(statistics.mean(values), 2),
        f"{prefix}_median": round(statistics.median(values), 2),
        f"{prefix}_min": min(values),
        f"{prefix}_max": max(values),
    }


def sum_membership(rows, change_type, column):
    total = 0
    for row in rows:
        if row["change_type"] != change_type:
            continue
        value = numeric_value(row.get(column))
        if value is not None:
            total += value
    return int(total)


def sum_row_values(rows, field):
    total = 0
    for row in rows:
        value = numeric_value(row.get(field))
        if value is not None:
            total += value
    return int(total)


def outlier_rows(comparison_rows, top_n, min_tracts_for_pct, min_population_for_pct):
    outliers = []
    common_rows = [row for row in comparison_rows if row["status"] == "common"]
    old_only_rows = [row for row in comparison_rows if row["status"] == "old_only"]
    new_only_rows = [row for row in comparison_rows if row["status"] == "new_only"]

    add_top_delta(
        outliers,
        "abs_tract_count_delta",
        common_rows,
        "old_tract_count",
        "new_tract_count",
        "tract_count_delta",
        "tract_count_pct_delta",
        top_n,
    )
    add_top_delta(
        outliers,
        "pct_tract_count_delta",
        common_rows,
        "old_tract_count",
        "new_tract_count",
        "tract_count_delta",
        "tract_count_pct_delta",
        top_n,
        minimum_old_value=min_tracts_for_pct,
        rank_by_pct=True,
    )
    add_top_delta(
        outliers,
        "abs_population_delta",
        common_rows,
        "old_total_population",
        "new_total_population",
        "population_delta",
        "population_pct_delta",
        top_n,
    )
    add_top_delta(
        outliers,
        "pct_population_delta",
        common_rows,
        "old_total_population",
        "new_total_population",
        "population_delta",
        "population_pct_delta",
        top_n,
        minimum_old_value=min_population_for_pct,
        rank_by_pct=True,
    )

    for column in RACE_COLUMNS:
        add_top_delta(
            outliers,
            f"abs_{column}_delta",
            common_rows,
            f"old_{column}",
            f"new_{column}",
            f"{column}_delta",
            f"{column}_pct_delta",
            top_n,
        )
        add_top_delta(
            outliers,
            f"pct_{column}_delta",
            common_rows,
            f"old_{column}",
            f"new_{column}",
            f"{column}_delta",
            f"{column}_pct_delta",
            top_n,
            minimum_old_value=min_population_for_pct,
            rank_by_pct=True,
        )

    for criterion, old_key, new_key, delta_key in (
        (
            "abs_connected_nodes_delta",
            "old_connected_nodes",
            "new_connected_nodes",
            "connected_nodes_delta",
        ),
        (
            "abs_connected_edges_delta",
            "old_connected_edges",
            "new_connected_edges",
            "connected_edges_delta",
        ),
        (
            "abs_orig_components_delta",
            "old_orig_components",
            "new_orig_components",
            "orig_components_delta",
        ),
        (
            "abs_orig_isolates_delta",
            "old_orig_isolates",
            "new_orig_isolates",
            "orig_isolates_delta",
        ),
        (
            "abs_nodes_contracted_delta",
            "old_nodes_contracted",
            "new_nodes_contracted",
            "nodes_contracted_delta",
        ),
    ):
        add_top_delta(
            outliers,
            criterion,
            common_rows,
            old_key,
            new_key,
            delta_key,
            None,
            top_n,
        )

    add_unmatched_outliers(
        outliers,
        "old_only_tract_count",
        old_only_rows,
        "old_tract_count",
        top_n,
        sign=-1,
    )
    add_unmatched_outliers(
        outliers,
        "old_only_total_population",
        old_only_rows,
        "old_total_population",
        top_n,
        sign=-1,
    )
    add_unmatched_outliers(
        outliers,
        "new_only_tract_count",
        new_only_rows,
        "new_tract_count",
        top_n,
        sign=1,
    )
    add_unmatched_outliers(
        outliers,
        "new_only_total_population",
        new_only_rows,
        "new_total_population",
        top_n,
        sign=1,
    )

    return outliers


def add_top_delta(
    outliers,
    criterion,
    rows,
    old_key,
    new_key,
    delta_key,
    pct_key,
    top_n,
    minimum_old_value=None,
    rank_by_pct=False,
):
    candidates = []
    for row in rows:
        old_value = row.get(old_key)
        delta_value = row.get(delta_key)
        pct_value = row.get(pct_key) if pct_key else ""
        if delta_value in ("", None, 0):
            continue
        if minimum_old_value is not None and (
            old_value in ("", None) or old_value < minimum_old_value
        ):
            continue
        rank_value = pct_value if rank_by_pct else delta_value
        if rank_value in ("", None, 0):
            continue
        candidates.append((abs(rank_value), row))

    for rank, (_, row) in enumerate(
        sorted(candidates, key=lambda item: item[0], reverse=True)[:top_n],
        start=1,
    ):
        outliers.append(
            outlier_row(
                criterion,
                rank,
                row,
                row.get(old_key),
                row.get(new_key),
                row.get(delta_key),
                row.get(pct_key) if pct_key else "",
            )
        )


def add_unmatched_outliers(outliers, criterion, rows, value_key, top_n, sign):
    candidates = [
        (abs(row[value_key]), row)
        for row in rows
        if row.get(value_key) not in ("", None, 0)
    ]
    for rank, (_, row) in enumerate(
        sorted(candidates, key=lambda item: item[0], reverse=True)[:top_n],
        start=1,
    ):
        value = row[value_key]
        old_value = value if sign < 0 else ""
        new_value = value if sign > 0 else ""
        outliers.append(
            outlier_row(criterion, rank, row, old_value, new_value, sign * value, "")
        )


def outlier_row(criterion, rank, row, old_value, new_value, delta_value, pct_value):
    return {
        "criterion": criterion,
        "rank": rank,
        "year": row["year"],
        "stem": row["stem"],
        "cbsa_code": row["cbsa_code"],
        "cbsa_title": row["cbsa_title"],
        "vintage": row["vintage"],
        "status": row["status"],
        "old_value": old_value,
        "new_value": new_value,
        "delta": delta_value,
        "pct_delta": pct_value,
        "old_path": row["old_path"],
        "new_path": row["new_path"],
    }


def assignment_fieldnames():
    fields = [
        "year",
        "status",
        "stem",
        "cbsa_code",
        "cbsa_title",
        "vintage",
        "filename_population",
        "definition_population",
        "component_counties_count",
        "old_path",
        "new_path",
        "old_tract_count",
        "new_tract_count",
        "tract_count_delta",
        "tract_count_pct_delta",
        "old_duplicate_tract_id_count",
        "new_duplicate_tract_id_count",
        "retained_tract_count",
        "removed_tract_count",
        "added_tract_count",
        "old_total_population",
        "new_total_population",
        "population_delta",
        "population_pct_delta",
    ]
    for column in RACE_COLUMNS:
        fields.extend(
            [f"old_{column}", f"new_{column}", f"{column}_delta", f"{column}_pct_delta"]
        )
    fields.extend(GRAPH_ASSIGNMENT_FIELDS)
    return fields


def membership_fieldnames():
    return [
        "year",
        "stem",
        "cbsa_code",
        "cbsa_title",
        "vintage",
        "change_type",
        "source_path",
        "tract_id_column",
        "tract_id",
    ] + list(POPULATION_COLUMNS) + list(TRACT_DETAIL_COLUMNS)


def graph_fieldnames():
    fields = [
        "year",
        "status",
        "stem",
        "cbsa_code",
        "cbsa_title",
        "vintage",
        "filename_population",
        "definition_population",
        "component_counties_count",
        "old_path",
        "new_path",
        "old_orig_path",
        "old_connected_path",
        "new_orig_path",
        "new_connected_path",
        "old_island_log_rows",
        "new_island_log_rows",
        "old_large_populated_overlap_rows",
        "new_large_populated_overlap_rows",
    ]
    for side in ("old", "new"):
        for stage in ("orig", "connected"):
            for field in GRAPH_STAT_FIELDS:
                fields.append(f"{side}_{stage}_{field}")
    for stage in ("orig", "connected"):
        for field in GRAPH_STAT_FIELDS:
            fields.append(f"{stage}_{field}_delta")
    fields.extend(
        [
            "old_nodes_contracted",
            "new_nodes_contracted",
            "nodes_contracted_delta",
            "old_edges_changed_from_orig_to_connected",
            "new_edges_changed_from_orig_to_connected",
            "edges_changed_from_orig_to_connected_delta",
            "old_population_changed_from_orig_to_connected",
            "new_population_changed_from_orig_to_connected",
            "population_changed_from_orig_to_connected_delta",
        ]
    )
    return fields


def summary_fieldnames():
    fields = [
        "year",
        "old_intersection_shp_count",
        "new_points_shp_count",
        "common_count",
        "old_only_count",
        "new_only_count",
        "old_unique_cbsa_count",
        "new_unique_cbsa_count",
        "common_unique_cbsa_count",
        "old_only_unique_cbsa_count",
        "new_only_unique_cbsa_count",
        "common_no_tract_change_count",
        "common_fewer_tracts_count",
        "common_more_tracts_count",
        "common_population_decrease_count",
        "common_population_increase_count",
        "common_orig_components_changed_count",
        "common_connected_nodes_changed_count",
        "common_connected_edges_changed_count",
    ]
    for prefix in (
        "old_tract_count",
        "new_tract_count",
        "old_total_population",
        "new_total_population",
        "old_connected_nodes",
        "new_connected_nodes",
        "old_connected_edges",
        "new_connected_edges",
    ):
        fields.extend([f"{prefix}_mean", f"{prefix}_median", f"{prefix}_min", f"{prefix}_max"])
    for column in POPULATION_COLUMNS:
        fields.extend(
            [
                f"common_added_{column}",
                f"common_removed_{column}",
                f"common_net_{column}",
                f"old_only_{column}",
                f"new_only_{column}",
            ]
        )
    return fields


def outlier_fieldnames():
    return [
        "criterion",
        "rank",
        "year",
        "stem",
        "cbsa_code",
        "cbsa_title",
        "vintage",
        "status",
        "old_value",
        "new_value",
        "delta",
        "pct_delta",
        "old_path",
        "new_path",
    ]


def main():
    args = parse_args()
    metadata = read_def_metadata(args.defs_root)
    old_outputs = read_outputs(args.old_root, args.years, args.vintage)
    new_outputs = read_outputs(args.new_root, args.years, args.vintage)
    island_counts = read_log_counts(args.out_root / "gen_duals_islands.csv")
    overlap_counts = read_log_counts(
        args.out_root / "gen_duals_large_populated_overlaps.csv"
    )

    comparison_rows = []
    membership_rows = []
    graph_rows = []

    for year in args.years:
        old_stems = set(old_outputs[year])
        new_stems = set(new_outputs[year])
        for stem in sorted(old_stems | new_stems):
            old_path = old_outputs[year].get(stem)
            new_path = new_outputs[year].get(stem)
            if old_path and new_path:
                status = "common"
            elif old_path:
                status = "old_only"
            else:
                status = "new_only"

            base = metadata_row(year, stem, status, old_path, new_path, metadata)
            old_frame = read_frame(old_path)
            new_frame = read_frame(new_path)
            graph_row = graph_structure_row(
                base, stem, old_path, new_path, island_counts, overlap_counts
            )
            row, old_id_column, old_rows, new_id_column, new_rows = comparison_row(
                base, old_frame, new_frame, old_path, new_path, graph_row
            )

            if status == "common":
                add_membership_rows(
                    membership_rows,
                    base,
                    old_path,
                    new_path,
                    old_id_column,
                    old_rows,
                    new_id_column,
                    new_rows,
                )

            comparison_rows.append(row)
            graph_rows.append(graph_row)

    summaries = summary_rows(comparison_rows, membership_rows, args.years)
    outliers = outlier_rows(
        comparison_rows,
        args.top_n,
        args.min_tracts_for_pct,
        args.min_population_for_pct,
    )

    write_csv(
        args.out_root / "assignment_comparison_by_cbsa.csv",
        comparison_rows,
        assignment_fieldnames(),
    )
    write_csv(
        args.out_root / "tract_membership_changes.csv",
        membership_rows,
        membership_fieldnames(),
    )
    write_csv(
        args.out_root / "assignment_summary_by_year.csv",
        summaries,
        summary_fieldnames(),
    )
    write_csv(
        args.out_root / "assignment_outliers.csv",
        outliers,
        outlier_fieldnames(),
    )
    write_csv(
        args.out_root / "graph_structure_comparison_by_cbsa.csv",
        graph_rows,
        graph_fieldnames(),
    )

    print(
        "Wrote "
        f"{len(comparison_rows)} CBSA comparison rows, "
        f"{len(membership_rows)} tract membership change rows, "
        f"{len(graph_rows)} graph comparison rows, "
        f"{len(summaries)} yearly summary rows, and "
        f"{len(outliers)} outlier rows."
    )


if __name__ == "__main__":
    main()
