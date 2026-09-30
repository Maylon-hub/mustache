---
hide:
  - toc
---

# MustaCHE

Visually explore CORE-SG hierarchies across density parameters, compare them
with HAI and preserve your analysis decisions. CORE-SG is the principal engine;
HDBSCAN is available as an auxiliary experimental baseline.

[Read the user guide](guia_documentacao.md){ .md-button .md-button--primary }
[Install the stable release](installation.md){ .md-button }
[Open GitHub](https://github.com/Maylon-hub/mustache){ .md-button }

## Exploration workflow

1. Choose a reproducible sample dataset or upload numeric CSV features.
2. Use CORE-SG and configure the mpts range, step size and distance metric.
3. Inspect the HAI Similarity Matrix and Meta-Hierarchy Dendrogram.
4. Compare representative hierarchies (medoids) in Reachability Plots.
5. Select branches, save the project and export relevant partitions.

## Scientific interpretation

HAI is the main hierarchy comparison. Exact and approximate analyses are
identified explicitly. A medoid represents a meta-cluster of hierarchies, not a
cluster of individual samples. Reachability geometry comes from each fitted
hierarchy; old shared OPTICS layouts are labeled as historical saved data.

Read the [scientific and usage guide](guia_documentacao.md),
[reproduction procedure](reproducao.md), and
[technical review](technical_review_2026-09-26.md) before treating the modern
full-tree representation as numerically identical to the legacy interval tree.

The stable `mustache-core==0.3.0` and `core-sg-mustache==0.4.5` packages are
available on TestPyPI, not official PyPI. CPython 3.11 on Windows x86-64 and
Linux x86-64 is qualified; macOS remains unqualified. Start with the
[installation guide](installation.md) or use the
[strict reproduction procedure](reproducao.md).
