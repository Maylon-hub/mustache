# Archived packaging and TestPyPI record

Historical date: 2026-09-18. This is not the current installation guide and
was not verified against TestPyPI in the 2026-09-26 review.

Recorded artifacts: core-sg-mustache 0.3.0 and mustache-core 0.2.0. CORE-SG's
wheel was cp311-cp311-win_amd64, with Python modules, Cython sources and
_mst_kruskal.cp311-win_amd64.pyd and _reweight.cp311-win_amd64.pyd.
MustaCHE's py3-none-any wheel contained Flask, core modules, templates and
static assets, excluding tests, reports and legacy sources.

Recorded CORE-SG build: cython>=3.0, numpy>=1.24,<3, setuptools>=77 and wheel;
MustaCHE used setuptools>=61.0. Historical requirements were Python>=3.10,
pandas>=2.0, scikit-learn>=1.3, hdbscan>=0.8.39, pynndescent>=0.5.13,
Flask>=3.0.0 and core-sg-mustache>=0.3.0. Use current pyproject files instead.

## Reported checks (not rerun here)

- C:/temp/venv_teste: downloaded the Windows/Python 3.11 CORE-SG wheel (165 kB),
  imported Cython and produced 299 MST edges.
- C:/temp/venv_mustache: reportedly installed mustache-core 0.2.0 and
  core-sg-mustache 0.3.0 and imported both packages.

Checks used TestPyPI with PyPI as an extra index. One native platform wheel
cannot establish compiler-free installation on Linux/macOS or other Python
versions. Source later added cibuildwheel/trusted-publisher workflows, but this
historical record does not prove every artifact was published. See
[Reproduction](reproducao.md) and [Technical review](technical_review_2026-09-26.md).
