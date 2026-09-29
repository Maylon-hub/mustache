# MustaCHE 0.3.0rc3 — unpublished RC proposal

Paired with `core-sg-mustache==0.4.5rc3`. CHANGELOG.md lists the previously
audited corrections consolidated here. This stage adds no scientific algorithm.

This RC restores the original tool's essential manual meta-dendrogram branch
selection: visible internal-node targets can be physically clicked, selected
groups and representatives update immediately, exports follow the active
selection, and reopening a saved project restores it. Real-browser pointer
tests now gate wheel and sdist qualification; synthetic Plotly events alone are
not accepted as interaction evidence.

## Official RC platform policy

Windows x86-64 and Linux x86-64 (glibc >= 2.28), **CPython 3.11 only**.
Windows has local qualification; Linux must pass GitHub Actions before upload.
macOS is NOT QUALIFIED / FUTURE WORK and is not a gate or an incompatibility
claim. Python 3.10, 3.12 and 3.13 are not advertised by this candidate.
Metadata now restricts Python to >=3.11,<3.12 as a deliberate RC support policy.

## Scientific scope

CORE-SG builds data hierarchies. HAI compares hierarchy structure; meta-clustering
uses `1 - HAI`; a medoid minimizes within-group distance sum. HDBSCAN is an
auxiliary baseline and internal tree/meta-clustering dependency. Exact HAI's
definition remains; sampled HAI is explicitly approximate. Modern full trees,
meta-clustering and reachability are not claimed equivalent to every legacy
Java/FOSC result or RNG. ARI/AMI/DBCV do not substitute HAI.

## Known limitations

- Exact CORE-SG stores dense distances; large datasets may exhaust memory.
- Sampled HAI may alter groups/representatives; retain seed and pair budget.
- Local single-user Flask app, not an authenticated multi-user server.
- Browser JS/CSS includes external CDN dependencies.
- Full legacy FOSC and experimental RNG equivalence are not delivered.
- Native `hdbscan==0.8.44` is pinned because `_tree_to_labels` is private.
- Only the dated readiness report establishes tested OS/Python combinations;
  CI configuration alone is not successful execution; pending Linux evidence
  must be obtained before promoting the Windows/Linux pair.

## Backward compatibility

Project schema 2 and old-parameter fallback remain. Saved results are not
automatically recomputed; old shared-OPTICS geometry is warned about. Python
imports and CLI remain. Unattributed historical CSVs are excluded from packages;
the programmatic sklearn catalog and seeded examples remain available.

## Breaking changes

No intentional API removal. Dependency resolution is tighter: exactly the
paired CORE-SG RC and native HDBSCAN release are required. Newly recomputed
results may differ from rc2 due to consolidated correctness fixes; saved old
numerical outputs are not rewritten.
