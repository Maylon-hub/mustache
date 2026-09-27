# Archived PIBIC delivery audit

Historical audit date: 2026-09-25. Superseded for current code by
[the technical review](technical_review_2026-09-26.md). Results below are
historical, not claims that the same tests passed again today.

## Original objectives and recorded status

| Objective | Recorded evidence | Limitation |
|---|---|---|
| Integrate CORE-SG | One fit and repeated hierarchy extraction | Public fast-path conventions needed further review |
| Compare performance | Benchmark scripts and reports | Historical numbers require reproduction |
| Validate clustering quality | ARI and AMI with external labels | DBCV was not implemented; none replaces HAI |
| Adapt views | HAI, meta-dendrogram, cuts, branch selection, reachability | One OPTICS layout was reused across mpts; corrected on 2026-09-26 |
| Documentation and training | Guide, notebook and report | Independent supervisor reproduction required |

## Historical evidence recorded on 2026-09-25

- MustaCHE: 66 passing pytest tests in Python 3.11; CORE-SG: 200 passing tests.
- Quickstart notebook executed in a Python kernel; CLI help and startup checked.
- Chrome headless checked four routes, images, an Iris batch and branch selection,
  with no severe console errors.
- Local candidate wheels mustache-core 0.3.0rc1 and core-sg-mustache 0.4.5rc1
  were reportedly installed together in a clean environment. Later source
  configuration targeted 0.3.0rc2 and 0.4.5rc2.

## Scientific-report corrections identified then

Do not describe the meta-dendrogram as average/UPGMA: current code uses single
linkage. Do not claim delivered DBCV, modern Docker deployment, identical
reachability at every mpts, or an unrerun benchmark as current evidence.
Distinguish historical pure-Python packaging from native Cython wheels and
installed distribution versions from source checkouts. Update test counts
only from an identified execution.

The earlier backend audit also recorded lazy SCORE-SG imports, preservation
of the complete k_max support graph during lower-k extraction and consolidated
release workflows. This record does not establish that publication succeeded.

## Independent acceptance procedure

Install identified artifacts in a clean environment; capture versions and
import paths; run both suites and the notebook; run a web batch; select a
branch, save/reopen/export; repeat equivalent small and medium benchmarks.
Check every manuscript claim against that evidence. Preserve the researcher's
self-contained bibliography.
