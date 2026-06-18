import argparse
import contextlib
import io
import os
import sys
import concurrent.futures.process as futures_process
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

MPLCONFIGDIR = Path("/private/tmp/capy-bara-matplotlib")
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))
os.environ.setdefault("MPLBACKEND", "Agg")

from pipeline import calculate_metrics

# The sandbox blocks this sysconf preflight, but worker process creation itself works.
futures_process._check_system_limits = lambda: None


DEFAULT_VINTAGE = "march_2020"
DEFAULT_SAMPLE = Path("cbsas/2020/186847_39460_march_2020_cbsa_tracts_connected.json")
DEFAULT_OUT_ROOT = Path("points_vs_intersection_exploration/outputs")
METRIC_RUNS = (
    ("white_black_old_intersection.csv", "old", "BLACK", "WHITE", "TOTPOP"),
    ("white_black_points.csv", "new", "BLACK", "WHITE", "TOTPOP"),
    ("white_poc_old_intersection.csv", "old", "POC", "WHITE", "TOTPOP"),
    ("white_poc_points.csv", "new", "POC", "WHITE", "TOTPOP"),
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run segregation metrics for March 2020 connected CBSA graph JSONs "
            "from the old intersection and representative-point outputs."
        )
    )
    parser.add_argument("--old-root", type=Path, default=Path("old_cbsas"))
    parser.add_argument("--new-root", type=Path, default=Path("cbsas"))
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--vintage", default=DEFAULT_VINTAGE)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, min(os.cpu_count() or 1, 4)),
        help="Worker processes used for graph metric calculations.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Print progress after this many metric rows; use 0 to disable.",
    )
    return parser.parse_args()


def connected_graphs(root, vintage):
    pattern = f"*_{vintage}_cbsa_tracts_connected.json"
    return sorted(root.glob(f"*/{pattern}"))


def calculate_row(task):
    path, x_col, y_col, tot_col, headers_only = task
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            calculate_metrics.run_metrics(
                str(path), x_col, y_col, tot_col, headers_only=headers_only
            )
    except ZeroDivisionError as error:
        return str(path), "", f"{path} {error}"
    finally:
        calculate_metrics._angle_1.cache_clear()
        calculate_metrics._angle_2.cache_clear()
        calculate_metrics.property_sum.cache_clear()

    return str(path), buffer.getvalue().strip(), ""


def write_metric_csv(paths, output_path, sample, x_col, y_col, tot_col, workers, progress_every):
    if not paths:
        raise ValueError(f"No connected graph JSONs found for {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _, header, header_error = calculate_row((sample, x_col, y_col, tot_col, True))
    if header_error:
        raise ValueError(header_error)

    tasks = ((path, x_col, y_col, tot_col, False) for path in paths)
    errors = []
    with output_path.open("w", newline="") as output:
        output.write(header + "\n")
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for index, (path, row, error) in enumerate(executor.map(calculate_row, tasks), 1):
                if error:
                    errors.append(error)
                elif row:
                    output.write(row + "\n")

                if progress_every and index % progress_every == 0:
                    print(
                        f"{output_path}: processed {index}/{len(paths)}",
                        file=sys.stderr,
                        flush=True,
                    )

    if errors:
        print(
            f"{output_path}: skipped {len(errors)} graph(s) with zero-division errors",
            file=sys.stderr,
        )
        for error in errors:
            print(error, file=sys.stderr)


def main():
    args = parse_args()
    roots = {
        "old": args.old_root,
        "new": args.new_root,
    }
    graph_paths = {
        side: connected_graphs(root, args.vintage) for side, root in roots.items()
    }

    for filename, side, x_col, y_col, tot_col in METRIC_RUNS:
        output_path = args.out_root / filename
        print(
            f"Writing {output_path} from {len(graph_paths[side])} graph(s)",
            file=sys.stderr,
            flush=True,
        )
        write_metric_csv(
            graph_paths[side],
            output_path,
            args.sample,
            x_col,
            y_col,
            tot_col,
            args.workers,
            args.progress_every,
        )


if __name__ == "__main__":
    main()
