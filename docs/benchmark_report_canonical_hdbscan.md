# Archived benchmark: CORE-SG versus reference-configured HDBSCAN

Historical execution: 2026-09-18 14:41. Recorded environment: Windows 10 Pro,
Python 3.11, MSVC v143; Cython active; three runs per scenario.
Reference report recorded medians, hdbscan 0.8.43, numpy 2.4.6,
scipy 1.17.1 and scikit-learn 1.8.0, with match_reference_implementation=True
and core_dist_n_jobs=1.

These observations predate the scientific corrections of 2026-09-26. They
were NOT rerun in that review and are not performance claims for current code.
The CORE-SG side times MST extraction while the HDBSCAN side fits complete
models; neither measures the full Flask/HAI/rendering workflow.

## Recorded batch observations (numerical entries preserved)

| Scenario | $n$ | $d$ | $k_{max}$ | Reference HDBSCAN (s) | CORE-SG (s) | Reference ratio | Faster method |
|:----------|----:|---:|------:|---------------------:|----------------------:|-----------------:|:---------|
| Baseline (n=300, d=5) | 300 | 5 | 15 | 0.2150 s | 0.0439 s | **4.90x** | Core-SG |
| Baseline (n=500, d=5) | 500 | 5 | 20 | 0.4524 s | 0.1059 s | **4.27x** | Core-SG |
| Baseline (n=1000, d=8) | 1,000 | 8 | 25 | 1.5794 s | 0.3218 s | **4.91x** | Core-SG |
| Baseline (n=2000, d=8) | 2,000 | 8 | 30 | 4.6962 s | 1.0255 s | **4.58x** | Core-SG |
| Baseline (n=5000, d=10) | 5,000 | 10 | 30 | 21.2178 s | 3.3532 s | **6.33x** | Core-SG |
| High dimensionality (d=35) | 1,000 | 35 | 30 | 4.3925 s | 0.9403 s | **4.67x** | Core-SG |
| High dimensionality (d=50) | 2,000 | 50 | 30 | 21.1160 s | 2.6178 s | **8.07x** | Core-SG |
| High dimensionality (d=100) | 2,000 | 100 | 30 | 17.5728 s | 2.6527 s | **6.62x** | Core-SG |
| Large sample count (n=10k) | 10,000 | 10 | 30 | 61.5025 s | 7.8046 s | **7.88x** | Core-SG |
| Large sample count (n=20k) | 20,000 | 10 | 30 | 198.7633 s | 200.4636 s | **0.99x** | ≈ Tie |
| Dense sweep (kmax=50) | 2,000 | 8 | 50 | 7.9438 s | 2.6620 s | **2.98x** | Core-SG |
| Dense sweep (kmax=100) | 2,000 | 8 | 100 | 16.9485 s | 10.5706 s | **1.60x** | Core-SG |
| $n$ | $d$ | $k_{max}$ | Earlier HDBSCAN (s) | Reference HDBSCAN (s) | Ratio for `match_ref` | Core-SG (s) | Earlier ratio | **Reference ratio** |
|----:|---:|------:|--------------------:|---------------------:|---------------------:|------------:|-----------------:|--------------------------:|
| 300 | 5 | 15 | 0.1623 s | 0.2150 s | **1.32x** | 0.0439 s | 3.74x | **4.90x** |
| 500 | 5 | 20 | 0.3237 s | 0.4524 s | **1.40x** | 0.1059 s | 3.16x | **4.27x** |
| 1,000 | 8 | 25 | 1.1559 s | 1.5794 s | **1.37x** | 0.3218 s | 2.94x | **4.91x** |
| 2,000 | 8 | 30 | 3.0215 s | 4.6962 s | **1.55x** | 1.0255 s | 2.91x | **4.58x** |
| 5,000 | 10 | 30 | 10.8398 s | 21.2178 s | **1.96x** | 3.3532 s | 3.37x | **6.33x** |
| 1,000 | 35 | 30 | 3.2291 s | 4.3925 s | **1.36x** | 0.9403 s | 3.66x | **4.67x** |
| 2,000 | 50 | 30 | 12.9292 s | 21.1160 s | **1.63x** | 2.6178 s | 5.20x | **8.07x** |
| 2,000 | 100 | 30 | 16.2139 s | 17.5728 s | **1.08x** | 2.6527 s | 6.40x | **6.62x** |
| 10,000 | 10 | 30 | 29.1752 s | 61.5025 s | **2.11x** | 7.8046 s | 3.80x | **7.88x** |
| 20,000 | 10 | 30 | 89.2771 s | 198.7633 s | **2.23x** | 200.4636 s | 0.45x | **0.99x** |
| 2,000 | 8 | 50 | 5.2342 s | 7.9438 s | **1.52x** | 2.6620 s | 2.06x | **2.98x** |
| 2,000 | 8 | 100 | 11.5786 s | 16.9485 s | **1.46x** | 10.5706 s | 1.13x | **1.60x** |

## Recorded reuse microbenchmark

For n = 2,000, d = 10 and k_max = 30, ten HDBSCAN sweeps versus one CORE-SG
fit followed by ten extraction sweeps: 53.27 s versus 8.58 s, recorded ratio 6.21x.
This was a script simulation, not browser timing. The current web request
reuses CORE-SG within a batch, not across separate batch requests.

## Interpretation limits

The former text claimed dimension-independent O(n log n) PyNNDescent cost,
sub-linear amortization and universal wins. Those claims are not established
by these measurements and do not describe the current exact CORE-SG path.
The current backend retains a dense distance matrix; memory is quadratic.
Reference configuration adjusts neighbor/cluster-size conventions and disables
approximate MST construction; it does not alone establish equivalence with
the original Java program or require a particular Prim/Kruskal backend.
A table mixing older means and newer medians cannot isolate one flag's causal
cost. Rerun equivalent workloads with correctness oracles before publishing
fresh comparisons. Original raw CSV observations remain unchanged.

See [Reproduction](reproducao.md) and [Technical review](technical_review_2026-09-26.md).
