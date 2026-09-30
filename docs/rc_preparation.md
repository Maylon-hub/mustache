# Reproducing the unpublished candidate

Pair **mustache-core 0.3.0rc3 + core-sg-mustache 0.4.5rc3**. No upload is implied.
Native HDBSCAN 0.8.44 is pinned: both projects use its private tree API, not just
scikit-learn's public HDBSCAN estimator. Future versions need qualification.

Official scope: Windows x86-64 and Linux x86-64, CPython 3.11 only. Linux wheels
target manylinux/glibc >= 2.28. Windows has local evidence; Linux must be
qualified on GitHub Actions before upload. macOS is NOT QUALIFIED / FUTURE WORK
and does not block this RC. Other Python versions require a later qualification.

1. Preserve Git HEAD, dirty patch, untracked files and SHA-256s for both checkouts.
2. Build CORE-SG wheel/sdist in a new build venv with a compatible C/C++ compiler.
3. Build MustaCHE wheel/sdist. Run `python -m twine check` on all four files.
4. Create a second venv **outside both checkouts**, with no system site packages.
5. From a neutral directory, install the CORE-SG wheel first, then the MustaCHE
   wheel. Do not set PYTHONPATH and do not use `pip install -e`.
6. Run `python -m pip check`, `python -m mustache.cli --help`, and inspect
   `mustache.__file__`, `core_sg.__file__` and the native extension locations.
7. Run `scripts/rc_smoke.py` with the installed interpreter from that directory;
   repeat installation from sdists in a third venv. Compiler required for CORE-SG.
8. Run full suites, `mkdocs build --strict`, and browser verification against
   the installed CLI using an isolated `MUSTACHE_PROJECTS_DIR`.

Build/runtime constraints and a dated readiness report identify qualified
versions. Archive `pip freeze`, downloaded dependency hashes, build logs and
artifact SHA-256s. Reproducible here means identifiable inputs and repeatable
installation/results; native wheel bit-for-bit reproducibility is not claimed.

## Publication is a separate decision

Validation runs on PR/push; publication workflows require explicit manual
dispatch, a validated CI run ID, a matching source SHA/version and environment
approval. No tag automatically publishes a package. Configure required checks
in GitHub branch rules separately; workflow YAML cannot impose branch protection.
The paired CORE-SG changes must first be made available to the MustaCHE CI's
companion source checkout. Until then remote integration CI cannot validate this
uncommitted pair. Local artifacts do not prove remote checks passed.

Citation roles and datasets are described in the repository-level AUTHORS.md
and DATASETS.md. Confirm author lists and ownership with the advisor/maintainers
before assigning a DOI or integrating into MIDAS. No RNG equivalence is claimed.
