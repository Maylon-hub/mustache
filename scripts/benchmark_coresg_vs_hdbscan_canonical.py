"""Benchmark extraction workloads, preserving historical scripts' scope.

Use --quick for a bounded smoke run; output goes to a new benchmark_runs directory.
Neither script measures full browser latency or proves clustering equivalence.
"""
import sys
import os
import time
import warnings
import json
import csv
import argparse
import platform
import core_sg
import importlib.metadata
from pathlib import Path

import numpy as np
import scipy
import sklearn

# Use the installed package or an explicitly configured PYTHONPATH.


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from sklearn.datasets import make_blobs
import hdbscan
from core_sg import CoreSG


def check_cython_backend():
    try:
        from core_sg._reweight import reweight_core_sg_from_lookup
        from core_sg._mst_kruskal import kruskal_mst_impl
        return True
    except ImportError:
        return False


CONFIGS = [
    # (n_samples, n_features, centers, k_max, Scenario)
    (300,    5, 3, 15, "Baseline (n=300, d=5)"),
    (500,    5, 4, 20, "Baseline (n=500, d=5)"),
    (1000,   8, 5, 25, "Baseline (n=1000, d=8)"),
    (2000,   8, 5, 30, "Baseline (n=2000, d=8)"),
    (5000,  10, 6, 30, "Baseline (n=5000, d=10)"),
    (1000,  35, 5, 30, "High dimensionality (d=35)"),
    (2000,  50, 5, 30, "High dimensionality (d=50)"),
    (2000, 100, 5, 30, "High dimensionality (d=100)"),
    (10000, 10, 6, 30, "Large sample count (n=10k)"),
    (20000, 10, 6, 30, "Large sample count (n=20k)"),
    (2000,   8, 5, 50, "Dense sweep (kmax=50)"),
    (2000,   8, 5, 100, "Dense sweep (kmax=100)"),
]

N_RUNS = 3
RANDOM_STATE = 42


def bench_hdbscan_canonical(X, k_max: int, n_runs: int) -> dict:
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        for k in range(2, k_max + 1):
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=2,
                min_samples=k,
                metric="euclidean",
                match_reference_implementation=True,
                core_dist_n_jobs=1,
                gen_min_span_tree=True,
                approx_min_span_tree=False,
            )
            clusterer.fit(X)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
    return {
        "median_s": float(np.median(times)),
        "mean_s":   float(np.mean(times)),
        "std_s":    float(np.std(times)),
    }


def bench_coresg(X, k_max: int, n_runs: int) -> dict:
    times = []
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        for _ in range(n_runs):
            t0 = time.perf_counter()
            core = CoreSG(metric="euclidean", p=2)
            core.fit(X, k_max=k_max)
            for k in range(2, k_max + 1):
                mst = core.extract_mst_from_core_sg(k=k)
            elapsed = time.perf_counter() - t0
            times.append(elapsed)
    return {
        "median_s": float(np.median(times)),
        "mean_s":   float(np.mean(times)),
        "std_s":    float(np.std(times)),
    }


def bench_interactive_session(X, k_max: int, n_interactions: int = 10) -> dict:
    # Reference HDBSCAN: 10 execuções do lote completo do zero
    t0 = time.perf_counter()
    for _ in range(n_interactions):
        for k in range(2, k_max + 1):
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=2,
                min_samples=k,
                metric="euclidean",
                match_reference_implementation=True,
                core_dist_n_jobs=1,
                gen_min_span_tree=True,
                approx_min_span_tree=False,
            )
            clusterer.fit(X)
    t_hdb = time.perf_counter() - t0

    # CoreSG: 1 fit() + 10 re-extrações do lote
    t0 = time.perf_counter()
    core = CoreSG(metric="euclidean", p=2)
    core.fit(X, k_max=k_max)
    for _ in range(n_interactions):
        for k in range(2, k_max + 1):
            mst = core.extract_mst_from_core_sg(k=k)
    t_csg = time.perf_counter() - t0

    return {
        "hdb_session_s": t_hdb,
        "csg_session_s": t_csg,
        "speedup": t_hdb / t_csg if t_csg > 0 else float("inf"),
    }


def load_previous_results(csv_path: Path) -> dict:
    prev_map = {}
    if not csv_path.exists():
        return prev_map
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (int(row["n_samples"]), int(row["n_features"]), int(row["k_max"]))
            prev_map[key] = {
                "hdbscan_prev_s": float(row["hdbscan_mean_s"]),
                "coresg_prev_s":  float(row["coresg_mean_s"]),
                "speedup_prev":   float(row["speedup"]),
            }
    return prev_map


def main():
    parser = argparse.ArgumentParser(description='MST-extraction workload benchmark (not full web latency)')
    parser.add_argument('--quick', action='store_true', help='Run one small scenario and a small reuse simulation')
    parser.add_argument('--output-dir', type=Path, default=Path('benchmark_runs') / time.strftime('%Y%m%d-%H%M%S'))
    args = parser.parse_args()
    configs = CONFIGS[:1] if args.quick else CONFIGS
    runs = 1 if args.quick else N_RUNS
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    cython_active = check_cython_backend()

    print("=" * 85)
    print("  Reference-configured extraction workload benchmark: Core-SG (Cython) vs HDBSCAN (Reference Implementation)")
    print("=" * 85)
    print(f"  Backend Cython: {'ACTIVE' if cython_active else 'FALLBACK PYTHON'}")
    print(f"  HDBSCAN: match_reference_implementation=True | core_dist_n_jobs=1")
    print(f"  Configuration: {len(configs)} scenarios x {runs} runs each (median)")
    print("=" * 85)
    print()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    prev_csv_path = out_dir / "benchmark_results.csv"
    prev_map = load_previous_results(prev_csv_path)

    results = []
    header = f"{'n':>6} {'d':>4} {'k_max':>6}  {'Reference HDB(s)':>16} {'CoreSG(s)':>12} {'Ratio':>13}   {'Faster method'}"
    print(header)
    print("-" * len(header))

    for n_samples, n_features, centers, k_max, category in configs:
        X, _ = make_blobs(
            n_samples=n_samples,
            n_features=n_features,
            centers=centers,
            random_state=RANDOM_STATE,
        )

        hdb = bench_hdbscan_canonical(X, k_max, runs)
        csg = bench_coresg(X, k_max, runs)
        speedup = hdb["median_s"] / csg["median_s"] if csg["median_s"] > 0 else float("inf")

        key = (n_samples, n_features, k_max)
        prev = prev_map.get(key, {"hdbscan_prev_s": 0.0, "coresg_prev_s": 0.0, "speedup_prev": 0.0})

        row = {
            "n_samples": n_samples,
            "n_features": n_features,
            "centers": centers,
            "k_max": k_max,
            "category": category,
            "hdbscan_canonical_median_s": hdb["median_s"],
            "hdbscan_canonical_mean_s": hdb["mean_s"],
            "hdbscan_canonical_std_s":  hdb["std_s"],
            "coresg_median_s": csg["median_s"],
            "coresg_mean_s":   csg["mean_s"],
            "coresg_std_s":    csg["std_s"],
            "speedup_canonical": speedup,
            "hdbscan_prev_s": prev["hdbscan_prev_s"],
            "speedup_prev":  prev["speedup_prev"],
            "cython_active": cython_active,
        }
        results.append(row)

        winner = "CoreSG" if speedup > 1.05 else ("HDBSCAN" if speedup < 0.95 else "≈ Tie")
        print(
            f"{n_samples:>6} {n_features:>4} {k_max:>6}  "
            f"{hdb['median_s']:>14.4f}s  {csg['median_s']:>10.4f}s  "
            f"{speedup:>11.2f}x   {winner}"
        )

    print()
    print("=" * 85)
    print("  REUSE MICROBENCHMARK (not browser latency)")
    print("=" * 85)

    session_n, session_k, interactions = (90, 6, 3) if args.quick else (2000, 30, 10)
    X_sess, _ = make_blobs(n_samples=session_n, n_features=10, centers=5, random_state=RANDOM_STATE)
    sess_res = bench_interactive_session(X_sess, k_max=session_k, n_interactions=interactions)
    sess_res.update(n_samples=session_n, k_max=session_k, interactions=interactions, runs=runs)
    print(f"  Reference HDBSCAN (complete model sweeps): {sess_res['hdb_session_s']:.2f}s")
    print(f"  Core-SG (one fit and extraction sweeps):          {sess_res['csg_session_s']:.2f}s")
    print(f"  Reuse timing ratio:             {sess_res['speedup']:.2f}x")
    print("=" * 85)

    # --- Salvar CSV Canônico ---
    csv_path = out_dir / "benchmark_canonical_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\nCSV saved to: {csv_path}")

    # --- Salvar Markdown em docs/ e na pasta da IC ---
    md_docs_path = out_dir / "benchmark_report_canonical_hdbscan.md"

    _write_markdown_report(md_docs_path, results, sess_res, cython_active)

    print(f"Markdown report saved to:")
    print(f"  1. {md_docs_path}")

    return results


def _write_markdown_report(path: Path, results: list, sess_res: dict, cython_active: bool):
    """Report only measured workloads, not unmeasured complexity guarantees."""
    import importlib.metadata
    canonical = 'hdbscan_canonical_median_s' in results[0]
    hkey = 'hdbscan_canonical_median_s' if canonical else 'hdbscan_mean_s'
    ckey = 'coresg_median_s' if canonical else 'coresg_mean_s'
    skey = 'speedup_canonical' if canonical else 'speedup'
    lines = [
        '# CORE-SG / HDBSCAN extraction workload benchmark', '',
        f'Execution: {time.strftime("%Y-%m-%d %H:%M")}; platform: {platform.platform()}; Python: {platform.python_version()}.',
        f'Cython active: {cython_active}; seed: {RANDOM_STATE}; runs: {sess_res["runs"]}.',
        f'Aggregation: {"median" if canonical else "mean"}. Reference conventions: {canonical}.',
        f'CORE-SG imported from: {core_sg.__file__}.',
        f'Installed hdbscan: {importlib.metadata.version("hdbscan")}; numpy: {np.__version__}.', '',
        'CAUTION: CORE-SG times support construction plus MST extraction, while HDBSCAN fits full models.',
        'This is not an equal end-to-end scientific workload or a web latency benchmark.',
        'No HAI, meta-clustering, frontend rendering or fresh label-equivalence validation is timed.', '',
        '| Samples | Features | k_max | HDBSCAN (s) | CORE-SG (s) | HDBSCAN / CORE-SG |',
        '|---:|---:|---:|---:|---:|---:|',
    ]
    for row in results:
        lines.append(f'| {row["n_samples"]} | {row["n_features"]} | {row["k_max"]} | {row[hkey]:.6f} | {row[ckey]:.6f} | {row[skey]:.4f} |')
    lines += ['', '## Reuse simulation',
        f'n={sess_res["n_samples"]}, k_max={sess_res["k_max"]}, sweeps={sess_res["interactions"]}.',
        f'HDBSCAN: {sess_res["hdb_session_s"]:.6f} s; CORE-SG: {sess_res["csg_session_s"]:.6f} s; ratio: {sess_res["speedup"]:.4f}.',
        'Reuses one CORE-SG instance across scripted sweeps; separate web batch requests do not share this cache.',
        'These observations do not establish universal speedups or dimension-independent complexity.']
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == '__main__':
    main()
