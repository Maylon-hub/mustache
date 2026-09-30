# MustaCHE 0.3.0

Stable `mustache-core==0.3.0`, paired with `core-sg-mustache==0.4.5` and
pinned `hdbscan==0.8.44`, is published on TestPyPI. Official PyPI publication
is deferred. The TestPyPI `0.3.0rc3` / `0.4.5rc3` pair remains the historical
immutable pre-release record. No new scientific or UI behavior was introduced
relative to the qualified RC; the final stable artifacts passed separate
Windows/Linux qualification.

## Highlights

- CORE-SG is the primary hierarchy engine. Fit once at maximum `mpts`, then
  reuse its support graph across the parameter sweep. HDBSCAN remains an
  auxiliary comparison baseline and an internal tree/meta-clustering component.
- HAI compares hierarchies. The meta-hierarchy groups them using `1 - HAI`;
  each group is represented by a medoid hierarchy.
- The Meta-Hierarchy Dendrogram supports visible, physical branch-node clicks,
  manual selection feedback and representative/Reachability updates.
- Project parameters and manual selection survive save, server restart and
  reopen. CSV and ZIP exports follow the active selection.
- End-to-end metric options remain Euclidean, Manhattan, Chebyshev, Minkowski
  with `p=2`, and cosine where the selected engine supports them. Invalid
  combinations are rejected rather than silently replaced.

## Supported platforms

Windows x86-64 and Linux x86-64 (glibc >= 2.28), **CPython 3.11 only**.
Both stable wheel/sdist paths passed clean-install, full-suite, docs
and physical-browser qualification. macOS and other Python versions are not
qualified, not declared incompatible.

## Known limitations and scientific scope

Exact CORE-SG uses dense distances and may exhaust memory on large datasets.
Sampled HAI is approximate and can change groups or representatives; retain
its seed and pair budget. The app is local single-user and loads some browser
assets from external CDNs. Full legacy FOSC parity, RNG reproduction and
experimental CORE-SG/RNG equivalence are not claimed. HAI is not replaced by
ARI, AMI or DBCV. The pinned native HDBSCAN release owns private
`_tree_to_labels` APIs; upgrades need compatibility testing.

## Backward compatibility and breaking changes

Project schema 2 and older-parameter fallback remain. Saved numerical results
are not silently recomputed; old shared-OPTICS geometry is warned about.
Python imports, CLI and export routes remain. No intentional API or schema
change is introduced relative to rc3. The companion dependency now points to
stable `core-sg-mustache==0.4.5` instead of the RC. Outputs may differ from
older pre-rc3 releases due to correctness fixes already present in rc3.

## Attribution

Maylon Martins de Melo is the author of this modern software release.
Murilo Coelho Naldi is credited for supervision and review; MIDAS is a
complementary research group. Original MustaCHE and CORE-SG authors and
papers remain separately credited in `AUTHORS.md` and `CITATION.cff`.
