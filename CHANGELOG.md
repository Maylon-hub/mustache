# Changelog

## 0.3.0 — Stable candidate (unpublished)

- Carry forward the scientifically and functionally qualified `0.3.0rc3`
  implementation without adding clustering, HAI or visualization algorithms.
- Keep CORE-SG as the primary engine with one reusable `k_max` support graph;
  HDBSCAN remains an auxiliary baseline and internal dependency.
- Preserve exact HAI and explicitly labeled sampled HAI, meta-hierarchy,
  representative medoids and hierarchy-specific Reachability Plots.
- Retain real-pointer manual dendrogram branch selection, visible feedback,
  saved/reopened selection and CSV/ZIP export behavior.
- Keep validated metrics and project persistence. Pin the stable companion
  `core-sg-mustache==0.4.5` and `hdbscan==0.8.44`.
- Requalify final wheel/sdist on Windows and Linux x86-64, CPython 3.11;
  macOS remains unqualified. Correct stable citation and Changelog metadata.

Known limitations: exact dense distances can exhaust memory; sampled HAI can
alter representatives; the Flask application is local single-user; full
legacy FOSC and RNG equivalence are not established.

## 0.3.0rc3 — TestPyPI pre-release

- Restore manual selection of meta-hierarchy branches with real clickable
  internal-node targets, immediate visual feedback, analysis/export integration
  and selection persistence after project reopen. Cover physical clicks with a
  browser E2E regression, including wheel and sdist qualification.

- Narrow official RC scope to Windows/Linux x86-64 and CPython 3.11;
  require fresh wheel/sdist qualification on both platforms before promotion.
  macOS is unqualified future work, outside publication gates.

- CORE-SG primary engine: build support once at `k_max`, reuse for the sweep;
  HDBSCAN remains auxiliary and an internal component.
- Preserve exact HAI; disclose deterministic pair-sampling metadata.
- Validate Euclidean, Manhattan, Chebyshev, Minkowski p=2 and cosine end to end.
- Derive reachability per hierarchy; explain medoids and distinguish outliers.
- Restore project parameters, provenance, groups and representatives.
- Improve branch selection, datasets, English UI/docs, assets and regression tests.
- Align package/citation versions, pin companion RC/native HDBSCAN, include
  release documentation and separate validation from manual publication.

This consolidates audited worktree changes, not changes already present in the
immutable rc2 artifacts. See RELEASE_NOTES.md.

## Earlier candidates

`0.3.0rc1` and `0.3.0rc2` remain historical tags. Consult those Git snapshots;
new fixes are not retroactively attributed to their artifacts.
