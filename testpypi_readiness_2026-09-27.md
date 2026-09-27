# TestPyPI readiness — Windows/Linux RC policy — 2026-09-27

## Decision and scope

Pair: **mustache-core 0.3.0rc3 + core-sg-mustache 0.4.5rc3**.
CORE-SG remains MustaCHE's principal engine; HDBSCAN remains an auxiliary
baseline/internal dependency. This stage changes qualification, distribution
policy and release gates, not scientific algorithms. No RNG work was performed.

This report supersedes the earlier platform/readiness decision in
`release_candidate_readiness_2026-09-27.md`. macOS absence is **not a blocker**.
Nevertheless, a configured Linux job is not a Linux qualification result.
No commit, staging, push, tag, release, transfer or upload was performed.

## Official target vs actually qualified matrix

| Platform | Python policy | MustaCHE | CORE-SG | Evidence/status |
|---|---|---|---|---|
| Windows x86-64 | CPython 3.11 | 0.3.0rc3 | 0.4.5rc3 | Local wheel/sdist qualification; details below |
| Linux x86-64 | CPython 3.11 | 0.3.0rc3 | 0.4.5rc3 | Official target; **PENDING real GitHub Actions qualification** |
| macOS | No qualified version | — | — | **NOT QUALIFIED / FUTURE WORK**, excluded from RC gates |

The actually tested public compatibility combination is **Windows 10 x86-64,
CPython 3.11.0**, both RC versions above. Linux is not yet a tested compatibility
claim. Python 3.10/3.12/3.13, ARM, Windows 32-bit, musllinux and PyPy are not
qualified by this RC. Both `Requires-Python` fields are `>=3.11,<3.12`; only
Python 3.11 and Windows/Linux classifiers are advertised. Portable macOS source
was not intentionally removed or declared incompatible.

Linux wheel target: manylinux x86-64 with glibc >=2.28. Required host test job:
Ubuntu 22.04 x86-64. Binary smoke also runs inside the cibuildwheel manylinux
build environment; neither step has run remotely for these changes yet.

## Windows evidence rerun in this stage

All runtime environments were newly created **outside both repositories**.
No editable installation, system-site-packages or PYTHONPATH was used. CORE-SG
was installed before MustaCHE; module/native-extension paths were asserted to
belong to the fresh interpreter prefix. Suites ran against installed production
packages using isolated copies of test/helper inputs, not source packages.

| Check | Result |
|---|---|
| MustaCHE installed wheel full suite | **131 passed**, 15.72 s |
| MustaCHE installed sdist full suite | **131 passed**, 15.86 s |
| CORE-SG installed wheel full suite | **222 passed**, 490.89 s |
| CORE-SG installed sdist full suite | **222 passed**, 513.37 s |
| `pip check`, both packages/both artifact kinds | Passed |
| Native `_mst_kruskal` / `_reweight` imports and repeat extraction | Passed for wheel and sdist installs |
| CORE-SG Euclidean + Manhattan | Passed for both kinds |
| MustaCHE CLI help + seeded minimal example | Passed for both kinds |
| Flask API, HAI, meta-clusters, medoids, per-hierarchy reachability | Passed for both kinds |
| Save, clear state/new app, reopen, parameter restoration, CSV/ZIP | Passed for both kinds |
| Auxiliary HDBSCAN baseline | Smoke passed for both kinds |
| MustaCHE MkDocs strict | Passed |
| CORE-SG Sphinx HTML | Passed; not presented as a new strict CI result |
| CFF schema validation | Both passed; authorship approval remains pending |
| `twine check`, artifact contents/privacy checks | All four artifacts passed |
| New promotion-policy tests | 17 per repository; included in the full suites |

Compiler: MSVC 14.51.36231 / Windows SDK 10.0.26100.0. Runtime exercised NumPy
2.4.6, SciPy 1.17.1, scikit-learn 1.9.1, native hdbscan 0.8.44; MustaCHE also
Flask 3.1.3, pandas 3.0.6 and Plotly 7.1.0. Per-install `pip freeze --all` and
command logs are retained; Windows records are not Linux dependency locks.

Private API owner: **native `hdbscan.hdbscan_._tree_to_labels`**, not sklearn's
HDBSCAN. `hdbscan==0.8.44` remains pinned in both packages; MustaCHE requires
exactly `core-sg-mustache==0.4.5rc3`. Broad transitive dependency ranges do not
mean every combination has been tested; preserve the actual CI freezes.

## CI, cibuildwheel and promotion status

- Both `.github/workflows/ci.yml` validate PR/push/manual runs on **Windows and
  Ubuntu 22.04 / Python 3.11 x64 only**. macOS cannot block these jobs. The old
  CORE-SG manual diagnostic was also aligned to 3.11. Branch required-check
  enforcement still needs GitHub branch-rule configuration by an owner.
- CORE-SG CI builds **one common sdist**, then cp311 Windows and repaired
  manylinux wheels, qualifies fresh wheel/sdist installs, runs full suites,
  native smokes and `pip check`, and retains JSON, logs and JUnit evidence.
- MustaCHE CI builds **one common wheel/sdist pair**, builds the companion
  CORE-SG on each OS, installs artifacts cleanly and runs the complete suite,
  CLI/example, Euclidean/Manhattan/API/persistence/export smoke and MkDocs strict.
- For final qualification, dispatch MustaCHE with the **immutable final
  CORE-SG commit SHA**, not just a moving `develop` ref. Both platform reports
  must identify the same companion SHA. Push/PR runs default to `develop` for
  development checks; they are not permission to publish a mismatched pair.
- cibuildwheel **3.3.1** is pinned in these build jobs. Locally verified build
  identifiers: `cp311-win_amd64`, `cp311-manylinux_x86_64`; macOS produced none.
  Linux architecture is x86_64, image `manylinux_2_28`; Windows is AMD64.
- The local Windows cibuildwheel attempt stalled obtaining Python 3.11.9 from
  NuGet and was stopped. The Windows wheel below was successfully built from
  the **same sdist** with `python -m build --wheel` and the local 3.11.0 compiler
  environment. This is **not** a claimed successful cibuildwheel binary run.
  Windows/Linux cibuildwheel completion remains part of the remote CI gate.
- Workflows passed actionlint 1.7.12 static validation; external shellcheck/
  pyflakes checks were disabled because those executables were unavailable.
  **No revised remote CI run has occurred.** Configuration is ready, results
  are not fabricated. Actual passing run IDs/URLs must be added later.
- TestPyPI/PyPI publication is separate, manual, defaults `publish=false`, and
  requires matching version tag, successful non-fork/non-PR CI, exact source SHA,
  Windows/Linux full-suite evidence and matching artifact SHA-256s. No tag
  automatically publishes. The new collector rejects missing Linux evidence,
  smoke-only reports, other Python/architectures, macOS, unrepaired Linux wheels,
  wrong source/companion SHAs and tampered artifacts. Local dirty-tree reports
  are not substitutes for this remote final-commit gate.

### Prepared workflows and human configuration

| Package | TestPyPI workflow/environment | Official PyPI workflow/environment |
|---|---|---|
| `core-sg-mustache` | `Maylon-hub/core-sg`, `wheels.yml`, `testpypi` | Same repository, `release.yml`, `pypi` |
| `mustache-core` | `Maylon-hub/mustache`, `release-testpypi.yml`, `testpypi` | Same repository, `release.yml`, `pypi` |

OIDC `id-token: write` is scoped to publishing jobs. Publisher account state,
project ownership and environment approvers were **not authenticated/verified**
in this task. Historical screenshots are not current credential evidence.
An owner must verify these exact Trusted Publisher tuples separately on
TestPyPI and PyPI; do not add the PyPI publisher to TestPyPI or vice versa.
No API token is needed if Trusted Publishing is configured correctly.

## Versions, tags, attribution and artifacts

At 2026-09-27 18:55 UTC, unauthenticated JSON checks returned HTTP404 for both
RC versions on [PyPI MustaCHE](https://pypi.org/pypi/mustache-core/0.3.0rc3/json),
[PyPI CORE-SG](https://pypi.org/pypi/core-sg-mustache/0.4.5rc3/json),
[TestPyPI MustaCHE](https://test.pypi.org/pypi/mustache-core/0.3.0rc3/json) and
[TestPyPI CORE-SG](https://test.pypi.org/pypi/core-sg-mustache/0.4.5rc3/json).
The corresponding `v0.3.0rc3`/`v0.4.5rc3` tags were absent locally and on the
queried origin refs. This is an observation, not a name/version reservation;
recheck immediately before any authorized upload/tag creation.

`CITATION.cff`, `AUTHORS.md`, CHANGELOG and release notes exist in both projects.
Historical scientific authors and implementation credits remain separate from
modern software attribution. **Authorship status: APPROVAL REQUIRED**, not a
technical schema failure. Each `AUTHORSHIP_APPROVAL_REQUIRED.md` identifies the
author list/order/collective/title/message/ownership fields needing advisor/MIDAS
confirmation. No ORCID, affiliation, institutional owner or author order was invented.

### Local artifact SHA-256 (not the later remote CI builds)

| File | Bytes | SHA-256 |
|---|---:|---|
| `mustache_core-0.3.0rc3-py3-none-any.whl` | 305633 | `38591b0d599f48cbbb781fb2d8d043167495c10ce977d92196db1e72c36b1d74` |
| `mustache_core-0.3.0rc3.tar.gz` | 748012 | `91b26c8e4037083330337e8c660e193f1706105de2a23ea3dd0d9b7926e4f4da` |
| `core_sg_mustache-0.4.5rc3-cp311-cp311-win_amd64.whl` | 177812 | `84eba9970c6b576532df2904e328a8d6f18c0f0734b2c627fb105fb4f175f011` |
| `core_sg_mustache-0.4.5rc3.tar.gz` | 112397 | `41076d269ab798ff2a60c846a389370bab8e20126dc3475a8d731defb06ed04e` |

MustaCHE wheel/sdist contain 36/77 file members; CORE-SG wheel/sdist contain
27/78. Both include release/legal/citation/provenance/approval files. MustaCHE
includes templates/static assets; CORE-SG wheel includes both compiled native
extensions, while its sdist has Cython sources instead of bundled binaries/C.
No Linux wheel is yet available. Manifests exclude legacy data, manuscripts,
benchmark outputs, caches and environments. Rebuilding does not promise
bit-for-bit identical native wheels; the table identifies the inspected files.

The dated local evidence directory `rc-windows-linux-20260927` outside both
repositories retains initial dirty-file checkpoint copies/diffs/SHA-256s,
artifact member inventories, fresh-venv command/freeze/JUnit logs, registry/tag
checks and redacted security scans. Final Git/hash inventory is retained there.
No evidence/cache/venv output is added to distribution packages.

Branches/unchanged starting HEADs: MustaCHE `mustache-core-sg` at
`40507f8e93bb29b5f64f38f41723d293b178d420`; CORE-SG `develop` at
`f5a716b202ced04ef3bf7a9abc9e1f12697cb4f1`. Tested local code includes preserved
**uncommitted changes**, so these HEAD hashes alone do not identify its contents.
Both self-contained bibliography copies retain SHA-256
`162277314efae1d3518657b2b6a70b6e5516e3c4e49e596426a5a94b53d6d861`.

## Security and logically separate commits

See `SECURITY_AUDIT_2026-09-27.md` in each repository: no secret/home-path alerts
in inspected artifacts; no secret alerts in audited HEAD/worktree snapshots;
18 historical MustaCHE Keen-demo key candidates require owner review, no CORE-SG
history alerts. Repository manuscript/signature/dataset rights and historical
personal paths remain human review items, not automatically erased by packaging.

Each `COMMIT_PLAN.md` assigns every dirty/new file once into logical scientific,
UI/persistence, test, documentation and packaging/CI/release groups. Protected
bibliography and existing research files are preserved. No staging/commit was
executed. Publication attribution and repository-sharing approval are distinct.

## Exact remaining human / execution checklist

### Before remote CI

1. Approve existing repository manuscript/privacy/dataset sharing findings before
   any push. Review historical demo-key ownership/revocation with the owner;
   no credential privileges were tested and no history rewrite is implied.
2. Explicitly authorize the proposed commit series and pushes, CORE-SG first.
3. Record final immutable CORE-SG SHA; dispatch its `ci.yml` and MustaCHE's
   `ci.yml` with that companion SHA. Obtain **successful Windows and Linux jobs**
   and retain run IDs, qualification JSON, logs/JUnit, freezes and hashes.
4. Inspect actual native tags and results. Update Linux status only after passing;
   fix any observed Linux failure before promotion. Do not broaden Python yet.

### Before TestPyPI publication

1. Complete the remote CI gate above. A failed/unrun Linux job cannot be waived
   by local Windows evidence; macOS is not required.
2. Obtain advisor/MIDAS/maintainer approval of both authorship proposals; if CFF
   or packaged attribution changes, rebuild and requalify the FINAL commit.
3. Verify ownership of `core-sg-mustache` / `mustache-core` and the exact TestPyPI
   Trusted Publishers above. Configure matching GitHub environments/approvers
   and required checks; no credential values should enter source or logs.
4. Recheck unused versions; explicitly authorize creation/push of matching tags
   `v0.4.5rc3` and `v0.3.0rc3` on qualified commits. No tag has been created here.
5. Separately authorize manual publication (`publish=true`, exact version and
   successful validation run ID), **CORE-SG first, then MustaCHE**. Promote only
   the qualified common sdist, native Windows/Linux wheels, and common MustaCHE
   wheel/sdist. Do not rebuild during promotion or upload macOS artifacts.
6. After upload, re-test fresh installations from TestPyPI. Download the two RC
   distributions explicitly from TestPyPI without dependencies, then install
   their local artifacts while resolving normal dependencies from PyPI. Avoid
   treating mixed public/test indexes as an interchangeable dependency source.

PyPI production, DOI/Zenodo and MIDAS repository ownership remain separate later
decisions; no production publication or institutional transfer is authorized.

## Final classification

| Classification | Answer | Concrete condition/blocker |
|---|---|---|
| Ready for commit | **YES** | Technical preparation ready; requires explicit owner authorization, no commit made |
| Ready for remote CI | **YES** | Workflows prepared; requires authorized push and immutable companion SHA |
| Ready for TestPyPI artifacts | **NO** | Linux native artifact and actual Windows/Linux cibuildwheel CI/evidence missing |
| Ready for TestPyPI publication | **BLOCKED** | Authorize remote qualification; obtain passing jobs, authorship/repository-sharing approval, Trusted Publisher/environment confirmation, and explicit tag/upload approval |

No macOS qualification is needed to change these last two answers. Once the
authorized remote jobs pass and human approvals/configuration are satisfied,
the prepared promotion gates can select the Windows/Linux RC artifacts for
TestPyPI without another broad scientific refactor.
