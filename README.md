# MustaCHE — Multiple Cluster Hierarchies Explorer

MustaCHE is a visual, interactive explorer centered on the CORE-SG engine.
It explores multiple density-based clustering hierarchies for a range of
`mpts` values, compares them with the Hierarchy Agreement Index (HAI), groups
similar hierarchies into meta-clusters and displays one representative hierarchy
(medoid) per group.

This repository modernizes the original MustaCHE by Antonio Cavalcante Araujo
Neto, Mario A. Nascimento, Joerg Sander and Ricardo J. G. B. Campello. The original
implementation is preserved in [legacy/](legacy/). The modern application uses
Python, Flask and Plotly with CORE-SG as the default engine. A separate HDBSCAN
engine is available as an auxiliary experimental baseline. Java is not required.
CORE-SG contains compiled Cython extensions, so the complete dependency stack is
not pure Python.

CORE-SG builds reusable support for extracting hierarchies at different density
parameters. HDBSCAN also supplies internal tree-processing routines and automatic
meta-clustering; those technical dependencies are separate from choosing the
HDBSCAN baseline engine. Baseline comparisons are scoped checks, not universal
requirements for CORE-SG behavior or substitutes for experiments against RNG.

## Current source and installation

The stable `mustache-core==0.3.0` and `core-sg-mustache==0.4.5` packages are
published on **TestPyPI**, not official PyPI. The qualified `0.3.0rc3` /
`0.4.5rc3` pair remains there as a historical pre-release record. HDBSCAN
`0.8.44` is an exact runtime dependency. See [release notes](RELEASE_NOTES.md),
[citation roles](AUTHORS.md), [dataset provenance](DATASETS.md), and the
[installation guide](docs/installation.md).

The stable releases are qualified on **Windows x86-64 and Linux x86-64**, with
**CPython 3.11 only**. The CORE-SG Linux wheel targets manylinux with glibc
>= 2.28. macOS is **not currently qualified / future work**, not known to be
incompatible. Python 3.10, 3.12 and 3.13 are not qualified for this release.

For normal use on Windows, create a fresh environment and install from
TestPyPI (PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --extra-index-url https://test.pypi.org/simple/ mustache-core==0.3.0
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\mustache.exe
```

Package metadata installs HDBSCAN, CORE-SG and the other runtime dependencies;
no separate manual installs are needed. `--extra-index-url` lets pip consider
both official PyPI and TestPyPI for dependency resolution. For strict source
isolation, use the [reproduction procedure](docs/reproducao.md), which obtains
only the two named distributions from TestPyPI and their dependencies from
official PyPI. On Linux, use `python3.11 -m venv .venv`, `.venv/bin/python`
and `.venv/bin/mustache`. A compatible CORE-SG binary wheel avoids compiling
its native extensions.

Open `http://127.0.0.1:5000`. The `mustache` CLI launches the local Web UI;
it has host, port and debug options, not batch-processing subcommands.

## Scientific workflow

1. Open **Datasets** for Iris, Wine, Breast Cancer Wisconsin or deterministic
   synthetic datasets, or upload a CSV with numeric features.
2. Keep the default **CORE-SG** engine, or choose **HDBSCAN (comparison baseline)**.
   Set **Minimum mpts**, **Maximum mpts**, **Step size** and
   **Distance metric**. Specify whether the CSV has a header when automatic
   detection is ambiguous.
3. Inspect the **HAI Similarity Matrix** and **Meta-Hierarchy Dendrogram**.
   The matrix uses increasing `mpts` order; dendrogram leaves may be reordered.
4. Use automatic meta-clustering or select a distance threshold. Clicking a
   branch with the selection tool switches to manual mode: its descendants
   form a meta-cluster and its representative is recalculated. Additional
   non-overlapping branches form additional groups; overlapping selections
   replace earlier groups.
5. Inspect **Reachability Plots** for representatives and separately identified
   meta-clustering outliers. Use the hierarchy inspector for any other `mpts`,
   with zoom and flat-cluster colors; point labels are local to that hierarchy.
6. **Save Analysis**, then reopen it from **Projects & History** without rerunning
   clustering. **Export CSV** exports selected hierarchies, or active
   representatives when there is no manual selection.

In batch mode, `mpts` controls both the density-neighborhood parameter and minimum
cluster size; the legacy application exposed minimum cluster size separately.
The maximum bound is inclusive when reached by the selected step; for example
2..8 with step 2 yields 2, 4, 6, 8. Require
`2 <= min_mpts <= max_mpts < n_samples` and a positive step.

Both algorithms support **euclidean, manhattan, chebyshev, minkowski (p=2)** and
**cosine** in this application. Cosine is a dissimilarity and requires non-zero
vectors. Angular, Pearson, supremum aliases and precomputed matrices are not
advertised as supported modern UI inputs. Invalid combinations return an error.

HAI remains the primary hierarchy comparison: it compares normalized sizes of
lowest-common-ancestor clusters for point pairs. Exact calculation is used up
to 2,000 samples. Larger analyses use deterministic sampled pairs, explicitly
labeled approximate and accompanied by a seed, sample budget, sampling method
and per-comparison error bound.

The representative hierarchy is the medoid minimizing the sum of distances
`1 - HAI` within its meta-cluster. It is not a representative data point.
ARI and AMI evaluate flat labels against supplied reference labels; DBCV is not
implemented. None replaces HAI.

Reachability geometry is now derived from each fitted hierarchy, using
adjacent-leaf merge heights. It is not a shared OPTICS layout. The first ordered
sample has no predecessor and is shown as undefined. Read the
[scientific guide](docs/guia_documentacao.md) for differences from the legacy
hierarchy representation and FOSC workflow.

## Python API

```python
import pandas as pd
from sklearn.datasets import make_blobs
from mustache.core import run_clustering
from mustache.core.batch import run_batch_clustering, analyze_batch_results

X, truth = make_blobs(n_samples=90, centers=3, random_state=42)
data = pd.DataFrame(X)
single = run_clustering(data, min_cluster_size=5, min_samples=5,
                        algorithm="core-sg", metric="manhattan",
                        true_labels=truth, compact=True)
results = run_batch_clustering(data, min_mpts=4, max_mpts=8, step=2,
                               algorithm="core-sg", metric="euclidean")
analysis = analyze_batch_results(results)
print(analysis["ordered_mpts"], analysis["medoids"])

# Optional comparison on the same dataset, sweep and metric:
# baseline = run_batch_clustering(data, 4, 8, 2,
#                                 algorithm="hdbscan", metric="euclidean")
```

CORE-SG builds its support once at `max_mpts`, then extracts each requested
hierarchy from that instance. A single-analysis t-SNE map uses Euclidean geometry
for visualization only; it does not affect clustering, HAI or representatives.
The [quickstart notebook](examples/mustache_quickstart.ipynb) provides another
executable example.

## Tests, evidence and limitations

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The suite includes known HAI values, symmetry, diagonal/range, sampled-pair
metadata, medoid selection, CORE-SG reuse and reference equivalence, metric
validation, saved projects, cuts and restoration. Test results and observed
limitations are recorded in the [technical review](docs/technical_review_2026-09-26.md).
Historical benchmark timings are not validation of the corrected checkout.

The current server is a single-user local research application with in-memory
analysis state. It is not a multi-user hosted service. Project JSON is stored
under `~/.mustache/projects`. New saves preserve parameters, complete hierarchy
results, HAI and meta-linkage, labels, representatives, selection and plot data.
Older saves remain readable, with unavailable metadata and older shared
reachability geometry identified honestly.

## License and credits

BSD 3-Clause; see [LICENSE](LICENSE). Original authors and scientific names retain
their original spelling. Modernization and CORE-SG integration: Maylon Martins
de Melo, supervised by Murilo Coelho Naldi, UFSCar (2025–2026).
