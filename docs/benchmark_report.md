# Archived benchmark: CORE-SG versus HDBSCAN

Historical execution: 2026-09-17 18:37. Recorded environment: Windows 10 Pro,
Python 3.11, MSVC v143; Cython active; three runs per scenario.
The first report recorded mean ± population standard deviation.

These observations predate the scientific corrections of 2026-09-26. They
were NOT rerun in that review and are not performance claims for current code.
The CORE-SG side times MST extraction while the HDBSCAN side fits complete
models; neither measures the full Flask/HAI/rendering workflow.

## Recorded batch observations (numerical entries preserved)

| n_samples | n_features | k_max | HDBSCAN (s) | Core-SG (s) | Speedup | Faster method | Scenario |
|----------:|-----------:|------:|------------:|------------:|--------:|:---------|:----------|
| 300 | 5 | 15 | 0.1623 ± 0.0016 | 0.0434 ± 0.0009 | **3.74x** | Core-SG | Baseline (n=300, d=5) |
| 500 | 5 | 20 | 0.3237 ± 0.0009 | 0.1025 ± 0.0001 | **3.16x** | Core-SG | Baseline (n=500, d=5) |
| 1,000 | 8 | 25 | 1.1559 ± 0.1132 | 0.3934 ± 0.0997 | **2.94x** | Core-SG | Baseline (n=1000, d=8) |
| 2,000 | 8 | 30 | 3.0215 ± 0.0172 | 1.0394 ± 0.0085 | **2.91x** | Core-SG | Baseline (n=2000, d=8) |
| 5,000 | 10 | 30 | 10.8398 ± 0.2187 | 3.2192 ± 0.0784 | **3.37x** | Core-SG | Baseline (n=5000, d=10) |
| 1,000 | 35 | 30 | 3.2291 ± 0.0011 | 0.8817 ± 0.0143 | **3.66x** | Core-SG | High dimensionality (d=35) |
| 2,000 | 50 | 30 | 12.9292 ± 0.0018 | 2.4844 ± 0.0117 | **5.20x** | Core-SG | High dimensionality (d=50) |
| 2,000 | 100 | 30 | 16.2139 ± 0.0063 | 2.5341 ± 0.0616 | **6.40x** | Core-SG | High dimensionality (d=100) |
| 10,000 | 10 | 30 | 29.1752 ± 0.3034 | 7.6689 ± 0.0969 | **3.80x** | Core-SG | Large sample count (n=10k) |
| 20,000 | 10 | 30 | 89.2771 ± 0.6314 | 197.0356 ± 3.5710 | **0.45x** | HDBSCAN | Large sample count (n=20k) |
| 2,000 | 8 | 50 | 5.2342 ± 0.0038 | 2.5404 ± 0.0187 | **2.06x** | Core-SG | Dense sweep (kmax=50) |
| 2,000 | 8 | 100 | 11.5786 ± 0.0169 | 10.2316 ± 0.1684 | **1.13x** | Core-SG | Dense sweep (kmax=100) |

## Recorded reuse microbenchmark

For n = 2,000, d = 10 and k_max = 30, ten HDBSCAN sweeps versus one CORE-SG
fit followed by ten extraction sweeps: 32.24 s versus 8.54 s, recorded ratio 3.77x.
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
