# Release candidate readiness — 2026-09-27

**Historical qualification snapshot.** The Windows/Linux-only policy and
current promotion status supersede this report in `testpypi_readiness_2026-09-27.md`.
The hashes below identify the earlier local artifacts; rebuilt scope-policy
artifacts have new hashes. macOS is no longer a publication gate.

MustaCHE **0.3.0rc3** with **core-sg-mustache 0.4.5rc3** passed local qualification
on Windows AMD64 / CPython 3.11.0. The installed wheels passed **114 MustaCHE
tests and 205 CORE-SG tests**. Fresh installation from both sdists, native
extension imports, CLI, strict documentation builds and the browser workflow
also passed. This is an unpublished candidate prepared from preserved dirty
worktrees. No commit, push, tag, GitHub release, package upload or repository
transfer was performed.

The dated local evidence bundle is `rc-preparation-20260927/` in the Codex
workspace. Only `rc-qualified/dist/` contains the qualified final distributions;
earlier build directories are intermediate attempts and must not be promoted.

## 1. Frozen starting state and preservation

| Repository | Branch | Starting and final Git HEAD | Starting worktree |
|---|---|---|---|
| MustaCHE | `mustache-core-sg` | `40507f8e93bb29b5f64f38f41723d293b178d420` | 33 tracked modifications; 6 untracked files; no removals |
| CORE-SG | `develop` | `f5a716b202ced04ef3bf7a9abc9e1f12697cb4f1` | 2 tracked modifications; 1 untracked file; no removals |

`initial-inventory.json` records branches, HEADs, remotes, local tags, every
starting dirty path and SHA-256, source-file hashes and original metadata.
`checkpoint/<repository>/files/` preserves the dirty files, including untracked
files. `unstaged.patch`, `staged.patch` and `against-head.patch` retain binary
Git diffs. `apply-manifest.json` lists every RC write and its before/after hash;
the application step checks branch, HEAD and all target hashes before writing
and retains a second backup. It makes no Git mutations and removes no files.

The corrected self-contained bibliography was preserved in both the repository
and external research-document folder. Both copies retain SHA-256:

`162277314efae1d3518657b2b6a70b6e5516e3c4e49e596426a5a94b53d6d861`.

The final inventory, dependency freezes, source hashes and artifact hashes are
in `final-evidence.json`; `final-state.json` and `final-diff/` record the resulting
uncommitted changes. These local checkpoint/evidence files are not package data.
Because these changes are uncommitted, the HEAD hashes alone do **not** identify
the RC code: retain the patches, snapshot hashes and artifact hashes together.

## 2. Version choice and dependency relationship

| Item | Before this preparation | Proposed candidate |
|---|---|---|
| MustaCHE source metadata | `0.3.0rc2` | `0.3.0rc3` |
| CORE-SG source metadata | `0.4.5rc2` | `0.4.5rc3` |
| Existing development environment | MustaCHE `0.3.0`, CORE-SG `0.4.4` | Preserved; use the new RC venvs for these tests |
| MustaCHE dependency on CORE-SG | Broad development constraint | `core-sg-mustache==0.4.5rc3` |
| Native HDBSCAN, both packages | Broad constraints | `hdbscan==0.8.44` |

Local and remote tags, GitHub releases and both package indexes were inspected
before choosing versions (`remote-versions.json`). MustaCHE tags reached
`v0.3.0rc2`; CORE-SG tags reached `v0.4.5rc2`. TestPyPI contained the two rc2
versions; official PyPI listed CORE-SG fork 0.4.4 and the MustaCHE project lookup
returned 404. Neither proposed rc3 version was found. GitHub release lists were
empty at inspection. Recheck availability immediately before a future upload.

Versions are aligned in pyproject metadata, installed `__version__`, CFF,
release notes, current documentation and qualified artifacts. Historical
versions/results remain explicitly historical. Modern “v2” denotes the
implementation generation, not a claim that the package version is 2.0.

## 3. What this preparation changed

The RC consolidates the prior scientific/functional audit; it introduces no new
clustering algorithm or HAI definition. CORE-SG remains the default and principal
visual exploration engine. HDBSCAN remains an auxiliary baseline and supplies
internal tree and meta-clustering components.

MustaCHE CHANGELOG and release notes describe support reuse, preserved HAI,
supported metrics, reachability derived from each hierarchy, representative
medoids, restored projects, English public UI/docs and regression coverage.
CORE-SG notes describe preservation of full `k_max` support, public-distance and
reference-compatibility corrections, existing adapter behavior and new tests.

RC-specific changes align versions and citation roles; freeze the qualified
dependencies; add clean-install smoke tests, artifact inspection and validation
CI; prepare manual publication; and narrow package contents. CORE-SG builds its
two extensions rather than collecting stale interpreter-specific binaries.
Generated C is excluded because it contained machine-specific include paths;
Cython regenerates it from distributed `.pyx` files during the source build.

Two RC regressions were added: installed metadata consistency and the real
private HDBSCAN signature/version contract. One existing CORE-SG source-inspection
test assumed the checkout was the working directory; it now inspects the imported
module's file, allowing the same assertion to run against an installed artifact.
A historical MustaCHE development script with a fixed personal checkout path is
excluded from the sdist and remains untouched in Git.

## 4. Changed files

These are RC-stage changes, in addition to the preserved starting modifications.
The complete initial and final dirty inventories and diffs remain in the bundle.

MustaCHE:

- `.github/workflows/ci.yml`, `docs.yml`, `release-testpypi.yml`, `release.yml`;
- `AUTHORS.md`, `CHANGELOG.md`, `CITATION.cff`, `DATASETS.md`, `MANIFEST.in`,
  `README.md`, `RELEASE_NOTES.md`, `pyproject.toml`, `mkdocs.yml`;
- `docs/rc_preparation.md`, `docs/reproducao.md`, `examples/rc_minimal.py`;
- `requirements/README.md`, `build-win-py311.txt`, `runtime-win-py311.txt`;
- `scripts/check_artifacts.py`, `collect_release_artifacts.py`, `rc_smoke.py`,
  `validate_promotion.py`;
- `tests/test_release_metadata.py` and this readiness report.

CORE-SG:

- `.github/workflows/ci.yml`, `docs.yml`, `release.yml`, `test.yml`, `wheels.yml`;
- `AUTHORS.md`, `CHANGELOG.md`, `CITATION.cff`, `DATASETS.md`, `MANIFEST.in`,
  `README.md`, `RELEASE_NOTES.md`, `pyproject.toml`, `setup.py`;
- `core_sg/__init__.py`, `docs/source/conf.py`,
  `docs/source/getting_started/installation.rst`;
- `requirements/README.md`, `build-win-py311.txt`, `runtime-win-py311.txt`;
- `scripts/check_artifacts.py`, `collect_release_artifacts.py`, `rc_smoke.py`,
  `run_installed_tests.py`, `validate_promotion.py`;
- `tests/integration/test_private_hdbscan_contract.py`,
  `tests/unit/test_hdbscan_adapter.py`.

## 5. Environment and reproducibility

Actual platform: **Windows 10 build 19045, AMD64, CPython 3.11.0**. Native build
used MSVC Build Tools 14.51.36231 / Windows SDK 10.0.26100.0. Build logs retain
the exact compiler invocation. Important build versions: setuptools 84.0.0,
wheel 0.48.0, Cython 3.3.0, build 1.6.1 and twine 7.0.0.

Actual runtime included numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1,
hdbscan 0.8.44, pandas 3.0.6, Flask 3.1.3, Plotly 7.1.0 and pynndescent 0.6.0.
Full build/runtime freezes are distributed under `requirements/`. These are
**Windows/Python 3.11 qualification records**, not universal dependency locks.
Broader metadata lower bounds were not all independently qualified.

New venvs `venvs/rc-wheel` and `venvs/rc-sdist` were created outside both
checkouts without system site packages. Dependencies were replayed from archived
wheelhouses; CORE-SG was installed first, followed by MustaCHE. No editable
installation or PYTHONPATH was used. Tests ran from neutral directories with
only test/benchmark inputs copied there. No production package source was copied
onto the test import path. Import checks located `mustache`, `core_sg` and both
native extensions under each venv's `Lib/site-packages`.

The sdist installation used pip's build isolation and compiled CORE-SG from
source. A sandbox cache-write denial required an authorized retry; the final
installation passed. Windows multiprocessing tests similarly required execution
outside the restrictive sandbox. Failures were not silenced or tests skipped.

The bundle archives dependency-wheel SHA-256s, source hashes, versions, commands,
logs and result data. Reproducible means identifiable inputs and repeatable
installation/behavior here; bit-identical native builds across compilers or
operating systems have not been demonstrated.

## 6. Final validation results

| Check | Observed result | Evidence in the local bundle |
|---|---|---|
| MustaCHE full installed suite | 114 passed, 14.39 s | `logs/rc-qualified-pytest-mustache.log`, JUnit XML |
| CORE-SG full installed Python/backend suite | 205 passed, 496.08 s | `logs/rc-qualified-pytest-core.log`, JUnit XML |
| Four project distribution builds | PASS | `logs/rc-qualified-build-*.log` |
| Four distributions, `twine check` | PASS | `logs/rc-qualified-twine.log` |
| Fresh wheel install and `pip check` | PASS | `logs/rc-qualified-install-*.log`, `rc-qualified-pip-check.log` |
| Fresh offline sdist install and `pip check` | PASS | `logs/rc-qualified-sdist-*.log` |
| Imports and both native extensions | PASS in both environments | CORE-SG smoke logs with module paths |
| CLI module and installed console entry point | PASS in both environments | CLI and console-script logs |
| Seeded minimum Python example | PASS for Euclidean and Manhattan | `logs/rc-qualified-example.log` |
| Installed integration scenarios | CORE-SG Manhattan/Euclidean and HDBSCAN Euclidean baseline PASS | Both MustaCHE smoke logs |
| MkDocs `build --strict` | PASS | `logs/rc-qualified-docs-mustache.log` |
| CORE-SG Sphinx `-E -W` | PASS, exit 0 | `logs/rc-qualified-docs-core.log` |
| CFF schema validation | Both PASS | `logs/rc-qualified-citation-*.log` |
| Offline workflow/guard checks | 26 checks PASS | `logs/rc-qualified-workflow-guards.log` |
| Browser interaction and rendering | 39 assertions PASS; no JS/asset errors | `qualified-web/browser/verification.json` |
| Actual CLI process restart | PASS; all three saved payloads identical | `qualified-web/verification.json`, `before-restart.json` |
| Distribution contents and privacy scan | Both wheel/sdist pairs PASS | `logs/rc-qualified-contents-*.log` |
| Final `git diff --check` | Recorded after application | `final-state.json` |

Sphinx emitted diagnostics from documentation extensions while returning
success; this is not a claim that every dependency emitted zero warnings.
GitHub Actions was **not executed** for these uncommitted changes. Offline guard
tests mock the GitHub run API and do not establish remote CI success.

The browser skills' requested CLI was unavailable; the existing Playwright
verification script was used with installed Chrome. It checked navigation,
images, CORE-SG defaults, metric selection, sidebar parameters, HAI, branch
selection, per-hierarchy inspection, threshold/manual modes, saving/reopening,
CSV, mobile overflow and console/network errors. Screenshots were inspected.

## 7. Installed scientific scenarios

Both metric scenarios used `make_blobs(n_samples=90, n_features=3, centers=3,
random_state=42)`, CORE-SG, `min_mpts=4`, `max_mpts=8`, `step=2`. Requested
hierarchies were `[4, 6, 8]`; each scenario selected medoid `mpts=6`.
Exact HAI used all 4,005 unordered pairs, retained original normalization and
reported `approximate=False`. Symmetry, unit diagonal and [0,1] bounds passed.
Each reachability result carried its own mpts and chosen metric.

The real HTTP scenario saved these two projects, stopped the installed CLI
process, started a new process and reopened from disk. Parameters, full analysis
and hierarchy results compared equal. Number of points remained 90; metric,
algorithm, bounds and step restored correctly. CSV had 90 rows and ZIP preserved
metadata, results, data and medoids. A third Iris/Manhattan browser project
restored its manual group, sidebar, HAI and representative plot after the same
restart. HDBSCAN received only auxiliary baseline qualification.

Scientific regressions include `test_hai_known_original_pair_sum`,
`test_medoid_minimizes_within_cluster_distance_and_ties`,
`test_reachability_is_adjacent_cophenetic_of_this_tree`,
`test_batch_fits_core_once_and_extracts_every_requested_mpts`,
`test_supported_metric_full_pipeline` and
`test_saved_project_restores_parameters_partition_and_plots` in MustaCHE's
`tests/test_scientific_review.py`. CORE-SG's public Euclidean regressions and
full validation suite also passed. These scoped cases do not prove universal
equivalence to RNG or every legacy implementation.

## 8. Private dependency and remaining scientific scope

`_tree_to_labels` belongs to **`hdbscan.hdbscan_` in the native `hdbscan`
distribution**, not scikit-learn's public HDBSCAN estimator. CORE-SG already
encapsulates it in `core_sg/hdbscan_adapter.py`; MustaCHE also calls it in
`mustache/core/clustering.py`. Previously broad dependency ranges could admit
untested private API changes. Both RCs now require exactly 0.8.44; signature,
installed extraction, real metric behavior and full suites were tested.
Other native HDBSCAN versions remain unqualified. A future upgrade requires
tests against actual dependencies; the adapter cannot guarantee compatibility.

Remaining differences from legacy are documented: CORE-SG replaces the old RNG
construction path; modern full single-linkage representation and automatic
meta-clustering are not certified equal to every legacy Java/FOSC result;
reachability now derives from each displayed hierarchy. Exact HAI remains the
principal hierarchy similarity measure; sampling is explicitly approximate.
ARI/AMI/DBCV are not substitutes. No fresh performance benchmark or general RNG
equivalence claim is made by this packaging qualification.

Dense exact distances retain quadratic memory cost. Sampled HAI can change
meta-groups/medoids. The Flask app is a local single-user tool with global active
analysis state, not an authenticated multi-user service. Browser assets still
use external CDNs. Full legacy FOSC and RNG experiments remain future work.

## 9. Artifact hashes and contents

These are the final local artifacts, not the earlier exploratory builds:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `core_sg_mustache-0.4.5rc3-cp311-cp311-win_amd64.whl` | 175665 | `d5b78899b8bd1e892cea11da1728147259e38e577c0236795af4172340098d12` |
| `core_sg_mustache-0.4.5rc3.tar.gz` | 105953 | `dae4c3cc9f443847ea4d7c4f1d32c8c94c099eaaca9b3996f4cc10f376ec7b21` |
| `mustache_core-0.3.0rc3-py3-none-any.whl` | 303432 | `5ddcb79ce00abc7a7023ac8c8befdf04058904b2db1cff94b5b3b33940d79e6b` |
| `mustache_core-0.3.0rc3.tar.gz` | 741309 | `cde3f8dd8c759e8bb85386f07d567901580aa2f8fcd6c4db548fc48970f958a8` |

The MustaCHE wheel has 35 archive entries: Python modules, templates, JS/CSS,
logos/images, metadata, license and citation/release/dataset documents. CORE-SG's
wheel has 26 entries, including `_mst_kruskal` and `_reweight` native extensions,
Python/pyx sources, metadata, license and third-party notices. Both sdists have
74 file entries with build inputs and relevant tests/helpers. Complete member
lists are retained in the contents logs.

No venv, cache, raw dataset, legacy executable, private research manuscript,
generated C, audit-result file, temporary log or local user-profile path was
found in these distributions. CORE-SG sdists contain no precompiled extensions.
Software-author attribution remains in public metadata by design. The minimal
MustaCHE sdist includes user/reproduction guides; the complete documentation
site and historical audit reports are built from Git, not the sdist.

## 10. Dataset provenance

Both `DATASETS.md` files record origin, original URL/DOI, redistribution terms,
loader changes and synthetic parameters/seeds. Iris, Wine, WDBC and Digits
attribution was checked against the original UCI pages and sklearn documentation.
The runtime catalog loads sklearn data programmatically; no copied raw research
dataset is in the packages. Derived feature-only exports require attribution.

Historical `8/100/500-amostras.csv` and labels lack a verified generator, seed
and license record. They remain in the checkout and are excluded from wheel/sdist.
CORE-SG notebooks/raw benchmark files are also excluded. Package exclusion does
not erase public Git history; review such material before an institutional move.
User-provided CSV loading does not grant redistribution rights.

## 11. Compatibility matrix

Only combinations actually exercised are listed:

| OS | Python | MustaCHE | CORE-SG | Status |
|---|---|---|---|---|
| Windows 10 AMD64 | CPython 3.11.0 | 0.3.0rc3 wheel | 0.4.5rc3 native wheel | PASS: clean install, full suites, CLI, browser, integration |
| Windows 10 AMD64 | CPython 3.11.0 | 0.3.0rc3 sdist | 0.4.5rc3 compiled from sdist | PASS: isolated source build/install, imports, pip check, CLI, both-metric integration smoke |

Linux, macOS and other Python versions are **not locally validated**. CI is
configured for Python 3.10–3.13 on three OS runners and portable cibuildwheel
builds, but configuration is not test evidence. Inherited macOS x86_64 wheel
test skipping is a release-qualification gap that needs a native test or an
explicitly narrowed published support set. Musllinux is not in the wheel target.

## 12. CI and publication status

Both new `ci.yml` workflows validate pushes, PRs and manual runs. They build,
install artifacts, check imports, run full installed suites and inspect packages.
MustaCHE also runs strict MkDocs and CLI; CORE-SG qualifies native backends and
builds portable wheels after validation. Tests are not allowed to fail silently.
Required branch checks must still be configured in GitHub rules by a maintainer.

TestPyPI and PyPI workflows are separate, manual-only and default `publish=false`.
Promotion requires a successful complete CI run from the same repository and
exact source SHA, the matching version tag and explicit version confirmation.
PR/fork, failed, incomplete and mismatched-source runs are rejected. They download
tested artifacts and do not rebuild during publishing. CORE-SG publishes portable
CI wheels and its selected sdist rather than unrepaired local Linux build wheels.
Documentation deployment also requires a manual decision.

These workflows have passed offline parsing/guard checks only. The paired rc3
CORE-SG source is still uncommitted locally; MustaCHE's remote companion checkout
cannot validate it until an authorized source update makes that exact revision
available. Freeze that companion SHA for final remote qualification. Artifact
availability/retention must also be checked before promotion.

## 13. Citation, authorship and release documents

Both CFF files pass schema validation and identify the modern software release,
with the original MustaCHE/CORE-SG articles as separate scientific references.
MustaCHE proposes Maylon plus the contributor collective; CORE-SG retains the
existing MIDAS team and adds Maylon's integration contributions. Historical
copyright, legacy implementation and third-party notices remain preserved.

`AUTHORS.md` distinguishes paper authors, implementation evidence, modernization
and supervision. Confirm individual names/aliases, author order, collective
names, affiliations/ORCIDs and the advisor's software contribution with the
advisor/MIDAS maintainers. These are proposed attributions, not an approved
authorship agreement. No release date, DOI, Zenodo deposit or endorsement has
been invented. CHANGELOG and release notes are prepared in both repositories,
with scientific scope, known limitations, compatibility and breaking changes.

## 14. Exact TestPyPI checklist — future authorized action

- [ ] Approve citation/ownership proposals and review this RC diff/checkpoints.
- [ ] Explicitly authorize commits/pushes/tags; retain the complete existing
  scientific fixes in those commits. Proposed branches:
  `release/mustache-0.3.0rc3` and `release/core-sg-0.4.5rc3` (not created).
- [ ] Make the companion CORE-SG rc3 source available first. Run both required
  CIs, including portable wheel jobs, and record immutable source SHAs/run IDs.
- [ ] Resolve untested wheel targets (including macOS x86_64) or narrow the
  publish set. Confirm all intended artifacts are present and hashes retained.
- [ ] Verify current TestPyPI Trusted Publishers in the account UI. MustaCHE:
  owner `Maylon-hub`, repository `mustache`, workflow `release-testpypi.yml`,
  environment `testpypi`, project `mustache-core`. CORE-SG: owner `Maylon-hub`,
  repository `core-sg`, workflow `wheels.yml`, environment `testpypi`, project
  `core-sg-mustache`. Names must exactly match the dispatched workflows/jobs.
- [ ] Configure GitHub `testpypi` environments, approval rules and OIDC access;
  add required CI checks in branch rules. Private account settings were not
  freshly inspected; historical screenshots do not prove their current state.
- [ ] Recheck both versions are unused; create authorized matching tags only
  after validation. Explicitly dispatch CORE-SG publication before MustaCHE,
  supplying the successful CI run ID, exact version and `publish=true`.
- [ ] From new environments, install stable dependencies from PyPI and the two
  exact candidates from TestPyPI with `--no-deps`; repeat pip check, module-path,
  native, CLI, web restart and metric/persistence/export scenarios. Retain logs.

## 15. Exact official PyPI checklist — future authorized action

- [ ] Complete and accept TestPyPI qualification and resolve all intended-platform
  failures. Confirm package ownership, license/third-party material, attribution,
  release notes, version and public source/documentation URLs.
- [ ] Approve the software author lists and institutional maintenance decision.
- [ ] Configure official Trusted Publishers: owner `Maylon-hub`, repository
  `mustache` or `core-sg`, workflow `release.yml`, environment `pypi` in each repo.
  MustaCHE's uncreated official project requires a pending publisher for
  `mustache-core`; CORE-SG's existing `core-sg-mustache` project requires project
  owner/maintainer access. A pending publisher does not reserve a package name.
- [ ] Configure protected GitHub `pypi` environments and required CI rules.
- [ ] Recheck version availability; explicitly authorize upload. Promote the
  exact approved tested artifacts, CORE-SG first, using same-SHA successful CI
  run IDs and matching tags. An RC is a prerelease, not a stable-version claim.
- [ ] Verify new official-index installation, imports, CLI and integration;
  verify classifiers, Python requirements, wheel tags, license and all URLs.
- [ ] Authorize GitHub release/public docs deployment separately. Decide whether
  to activate Zenodo, archive the qualified release and add its real DOI to CFF
  and release notes; no placeholder DOI should be presented as issued.

Trusted Publishing configuration follows the
[PyPI publisher setup](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
and [GitHub workflow guidance](https://docs.pypi.org/trusted-publishers/using-a-publisher/).
No account credentials or settings were changed in this preparation.

## 16. Exact MIDAS integration checklist and plan

- [ ] Confirm destination organization, repository names and maintainers with
  Murilo/MIDAS. Existing CORE-SG upstream is `midas-core-sg/core-sg`.
  Proposed MustaCHE destination `midas-core-sg/mustache` is a proposal, not a
  verified institutional decision or created repository.
- [ ] For CORE-SG, prepare a focused PR from the fork's corrected branch into
  the existing upstream. Preserve commits and review fork distribution-name,
  citation and compatibility choices; do not transfer a fork over that repo.
- [ ] For MustaCHE, choose an authorized repository transfer if institutional
  ownership is desired, preserving history/issues/tags/releases. Alternatively,
  keep personal ownership and establish an institutional fork with reviewed PRs.
  Avoid copying files into an unrelated new Git history.
- [ ] Review existing Git history for unknown dataset rights, private research
  material and accidental credentials before transfer. Package exclusions alone
  do not resolve repository-history ownership.
- [ ] Agree who maintains algorithm code, UI, CI, releases and documentation;
  confirm Maylon/Gabriel/other contributor identities and the advisor's role.
- [ ] Preserve current development branches and use reviewed release branches;
  protect institutional branches with the actual CI checks.
- [ ] Retain initial distribution names unless an explicit namespace migration
  is approved. `core-sg` and `core-sg-mustache` share an import namespace and
  must not be co-installed. Align upstream packaging before changing ownership.
- [ ] After an authorized move, update source/issues/docs URLs, CFF, Pages links
  and package project URLs. Reconfigure Trusted Publisher owner/repository claims
  on **both** indexes; redirects do not preserve OIDC trust configuration.
- [ ] Decide canonical releases/docs/Zenodo ownership and issue links to the
  actual release and DOI after they exist. No transfer, fork creation or PR was
  executed during this task.

## 17. Remaining blockers and recommended next steps

Local qualification is complete. External readiness depends on approved source
commits, successful remote CI/portable wheels, private publisher configuration,
author/ownership approval and actual TestPyPI installation. Wider dependency
ranges/platforms, large-data performance and RNG/FOSC comparisons require
separate qualification. Historical benchmarks and prior notebook executions
were not reclassified as new RC evidence.

The next five steps are: review/approve the frozen diff and authorship; authorize
paired commits with an immutable companion SHA; run remote required CI and resolve
wheel coverage; configure/verify publishers and authorize TestPyPI qualification;
then decide official PyPI and institutional integration using the checklists.

| Classification | Answer | Concrete blocker |
|---|---|---|
| Ready for local RC | **YES** | No remaining local qualification failure in the tested combination; retain the uncommitted source snapshot with artifacts |
| Ready for TestPyPI | **BLOCKED** | RC source not committed/available to remote paired CI; remote/portable-wheel CI not run; intended wheel coverage and publisher settings need confirmation; proposed attribution needs approval |
| Ready for PyPI | **BLOCKED** | TestPyPI qualification pending; official publisher/ownership and attribution approvals pending; intended-platform qualification pending |
| Ready for MIDAS integration | **BLOCKED** | Destination/ownership/maintenance decisions and upstream PR acceptance pending; repository-history data rights review pending |
