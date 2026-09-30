# Dataset provenance and distribution policy

Checked against the sources below on 2026-09-27. No raw research dataset is
embedded in the wheel or sdist. The UI loads sklearn's feature matrices at
runtime, discards target labels and keeps original units (no normalization).
CSV downloads add column names; they are derived feature-only exports, not the
original dataset files. Keep this attribution with redistributed exports.

| Catalog entry | Origin and license | Modification / reproducibility |
|---|---|---|
| Iris | R. A. Fisher, 1936; [UCI](https://archive.ics.uci.edu/dataset/53/iris), DOI 10.24432/C56C76; CC BY 4.0 | `load_iris`, sklearn-corrected version, 150x4; no random seed |
| Wine | S. Aeberhard and M. Forina, 1992; [UCI](https://archive.ics.uci.edu/dataset/109/wine), DOI 10.24432/C5PC7J; CC BY 4.0 | `load_wine`, 178x13; no random seed |
| Breast Cancer Wisconsin (Diagnostic) | W. Wolberg, O. Mangasarian and Street contributors, 1993; [UCI](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic), DOI 10.24432/C5DW2B; CC BY 4.0 | `load_breast_cancer`, 569x30, no IDs or diagnostic targets in features; no random seed |
| Two Moons | sklearn `make_moons`; generated synthetic data | 500 points, noise=.06, seed=42 |
| Concentric Circles | sklearn `make_circles`; generated synthetic data | 500 points, noise=.035, factor=.45, seed=42 |
| Four Blobs | sklearn `make_blobs`; generated synthetic data | 500 points, centers=4, std=.75, seed=42 |
| Quickstart and RC smoke example | sklearn `make_blobs`; generated synthetic data | 90x3, centers=3, seed=42 |

The UCI pages explicitly permit sharing/adaptation under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). sklearn is BSD-3-Clause;
its [dataset documentation](https://scikit-learn.org/stable/datasets/toy_dataset.html)
describes loader transformations. Record the installed sklearn version when
reproducing synthetic arrays. Generated examples are released with this project's
BSD-3-Clause code; no third-party raw data is copied for them.

Historical `datasets/8-amostras.csv`, `100-amostras.csv`, `500-amostras.csv` and
their `8-labels.csv`, `100-labels.csv`, `500-labels.csv` companions have no verified
generator/seed/license record. They are preserved in the checkout, **excluded
from wheel/sdist**, and are not approved release examples. The old datasets README
named absent files; use the catalog instead. All legacy data and private research
manuscripts are likewise excluded. Public Git history still requires owner review
before transfer; package exclusion does not erase repository history.
