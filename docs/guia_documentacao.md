# MustaCHE user and scientific guide

MustaCHE compares density-based hierarchies generated for different `mpts`
settings on the same indexed samples. It preserves the original exploration
workflow through CORE-SG, the default and principal engine, and interactive
Plotly views. A separate HDBSCAN engine is an auxiliary comparison baseline.

## HAI is the hierarchy comparison

For a hierarchy H, let d_H(i,j) be the size of the lowest cluster containing
both indexed samples, divided by n. HAI is

`HAI(H1,H2) = 1 - (2/n²) Σ(i<j) |d_H1(i,j) - d_H2(i,j)|.`

This normalization is retained from `legacy/mustache/resources/hai.pyx`.
Changing it to a mean over unordered pairs without the factor (n−1)/n would
change HAI. The dense helper's diagonal convention (1/n) does not contribute to
HAI because it is identical in both hierarchies. The HAI matrix itself has a
diagonal of exactly 1, is symmetric and lies in [0,1].

HAI compares hierarchy structure, not merge-height differences or flat-label
accuracy. It has not been replaced by TED, APTED, RTED, ARI, AMI or DBCV.
Adapting tree edit distance to this purpose is unvalidated future work.

The modern input is the fitted full single-linkage tree. Equal-height binary
merges are treated as one simultaneous density-level cluster, so arbitrary
serialization of a tied MST does not alter the comparison. The legacy
`hierarchy_tree.pyx` reads an interval hierarchy and gives distance zero to points
in the same terminal leaf. The inspected legacy launcher passes `compact=False`
to Java; this flag alone does not establish equivalence of its terminal leaves
to modern singleton leaves. Therefore the formula is preserved, but
exact equality with every Java-generated hierarchy is not
claimed. Equivalent representations and sample indexing are required to
compare numerical results.

### Exact and sampled calculations

Up to 2,000 samples, the calculation evaluates every unordered distinct pair
in float64. Above this threshold, it samples 50,000 uniform ordered distinct
pairs **with replacement**, using NumPy PCG64 with seed 42. All hierarchies use
the same sampled pairs.

The estimator is `1 - ((n−1)/n) * mean(pairwise differences)`.
The reported Hoeffding 95% absolute error bound applies to **each comparison**,
not simultaneously to the entire matrix or the stability of meta-cluster
assignments. Metadata records method, approximation status, n, pair count, seed,
generator, normalization, tie policy and bound scope. The public Python HAI API
allows overriding the exact threshold, budget and seed.

Approximate analyses can change representatives or meta-clusters when distances
are close. Repeat with larger budgets or exact calculation when scientifically
necessary. UI color-scale changes alter display contrast only: fixed 0–1,
adaptive observed range, or robust range clipping the lowest 10% of off-diagonal
values. Numeric HAI values are always available on hover.

## Meta-clustering and medoids

Meta-clustering treats each hierarchy as one object, using distance `1 - HAI`.
The modern default uses scikit-learn HDBSCAN with min_samples=1, minimum cluster size 2 and
single-cluster allowance. The Meta-Hierarchy Dendrogram uses SciPy single linkage
on the same distances. This is an explicit modern choice, not a promise of the
same legacy HDBSCAN/FOSC partition under every setting.
HDBSCAN here groups hierarchy objects using HAI. This internal analysis stage
does not change CORE-SG's role as the main engine that constructs the data
hierarchies. CORE-SG also reuses HDBSCAN's MST and tree-processing components.

For meta-cluster C, the medoid is the member minimizing
`Σ(j in C) (1 - HAI(i,j))`. It represents a **hierarchy**, identified by `mpts`,
not a data point. Ties choose the first member in increasing `mpts` order.
The criterion is equivalent to `compute_medoid_elements` in
`legacy/mustache/resources/hierarchies.py`.

One representative per group limits visual redundancy. Automatic meta-clustering
outliers (label −1) are displayed separately and are not medoids. A distance
threshold creates a different partition with a medoid for each resulting group;
it does not produce HDBSCAN noise labels. The UI explicitly selects automatic
or threshold mode, and shows a cut line only in threshold mode.

Manual branch selection defines non-overlapping meta-clusters from the clicked
subtrees and updates their medoids immediately. A new ancestor/descendant
selection replaces overlapping selected groups. Unselected hierarchies are not
automatic outliers. Selected descendants are also saved and exported. This does
not select clusters of dataset points. Full legacy FOSC controls are not exposed.
Inspect any hierarchy opens a zoomable detailed plot with flat-cluster colors,
black for noise, and hover sample indices, including non-medoids and outliers.
Cluster colors do not imply corresponding clusters across different mpts.

## Reachability Plots

Every plot corresponds to its displayed `mpts` and fitted hierarchy. Samples
are ordered by that tree's leaves; each bar is the merge height (cophenetic
distance) of adjacent ordered leaves. This reconstructs the density-contour
intent of legacy hierarchy-interval plots on the modern full tree.

This geometry is **not OPTICS**. The previous implementation cached one OPTICS
ordering and distance vector and changed only the labels for other `mpts`;
those plots could not be interpreted as each representative's own geometry.
New analyses do not use that cache. The first sample has no predecessor, so its
bar is missing rather than a fabricated ceiling.

An older project's saved OPTICS arrays remain viewable without recomputation,
with a visible warning that geometry may be shared across `mpts`. Distances
from a full tree need not match the legacy interval hierarchy's bars exactly.

## Configure an analysis

**Algorithm:** CORE-SG is the main workflow. It builds support once at the
requested maximum `mpts` and reuses it for extraction. The auxiliary HDBSCAN
baseline directly fits each requested hierarchy for comparison.
Both preserve noise labels; CORE-SG's optional noise reassignment is disabled.
Flat partitions use HDBSCAN reference-compatible selection on each tree with
the requested minimum cluster size.

**Minimum mpts / Maximum mpts / Step size:** sweep
`range(min_mpts, max_mpts + 1, step)`. The maximum is a configured bound, not
necessarily an evaluated value when the step does not land on it. Require at
least three samples, `2 <= min_mpts <= max_mpts < n_samples`, and step >= 1.
In batch mode minimum cluster size and density `mpts` are both set to each
sweep value. The legacy form exposed minimum cluster size independently; this
modern coupling can change flat partitions and is not legacy parameter parity.
Small settings show fine structure and noise; large settings
emphasize denser, coarser structures. Explore a small sweep before a large one.

**Distance metric:** the end-to-end supported set for both algorithms is
euclidean, manhattan, chebyshev, minkowski with p=2, and cosine.
Minkowski p=2 is equivalent to Euclidean; arbitrary p is not exposed.
HDBSCAN cosine uses the generic distance path, and zero vectors are rejected.
Supremum corresponds conceptually to Chebyshev, but old aliases, angular and
Pearson are not accepted. Backend support alone is not an end-to-end guarantee.

Clustering, mutual reachability and hierarchy plots all use the chosen metric.
The optional single-analysis t-SNE map uses Euclidean distance for visualization,
with seed 42; it does not define any clustering result. A failed projection
falls back to feature coordinates and is labeled accordingly. No UMAP is
implemented.

**CSV:** numeric features only; labels are not automatically excluded from a
numeric column. For the single-analysis API, provide reference labels separately
as `labels_file` for ARI and AMI. Numeric CSV headers can look like data: select
the explicit CSV-header option when needed. Missing/infinite feature values
return an error.

## Save, reopen and export

Save Analysis records a name, dataset name, sample count, algorithm, metric,
minimum/maximum `mpts`, step, observed time and timestamp. The result payload
contains HAI and its metadata, meta-linkage, active labels/medoids/outliers,
automatic partition, threshold, manual selection and every hierarchy's labels,
probabilities and geometry.

Projects & History reopens the saved data without clustering again. The sidebar
and all coordinated views restore the active parameters and selection.
Older project aliases are supported; missing parameters are inferred only where
possible, and unavailable values are displayed as missing. Export CSV uses
manually selected hierarchies, otherwise active representatives. Export ZIP
includes metadata, results and the saved dataset.

## Python API and reproducibility

```python
import pandas as pd
from sklearn.datasets import make_blobs
from mustache.core.batch import run_batch_clustering, analyze_batch_results

X, _ = make_blobs(n_samples=90, n_features=3, centers=3, random_state=42)
results = run_batch_clustering(pd.DataFrame(X), 4, 8, 2,
                               metric="manhattan", algorithm="core-sg")
analysis = analyze_batch_results(results)
assert analysis["ordered_mpts"] == [4, 6, 8]
print(analysis["hai_computation"], analysis["medoids"])
```

For one hierarchy, `mustache.core.run_clustering` accepts
`min_cluster_size`, `min_samples`, `metric`, `algorithm`, `true_labels`
and `compact`. Results contain labels, probabilities, linkage, geometry,
metric and sample metadata. `compact=True` omits expensive individual
dendrogram/map figures. The deprecated `precomputed_optics` parameter is accepted
but not used; callers receive a deprecation warning.

See [Reproduction](reproducao.md) and the
[review with original-to-modern mapping](technical_review_2026-09-26.md).
The Portuguese PIBIC manuscript and development-context notes are retained as
research records, excluded from the English public documentation site.
