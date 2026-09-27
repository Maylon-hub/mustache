# Proposed commit plan — not executed

MustaCHE branch `mustache-core-sg`, base HEAD `40507f8e93bb29b5f64f38f41723d293b178d420`.

This plan includes existing uncommitted corrections and this qualification task.
No staging, commit, push, tag or history rewrite has been performed. Review the
complete diff before any authorized staging; do not discard user changes.
Each file is assigned once. Some files contain previously audited fixes together
with release edits; split hunks only if the owner requests a finer history.
Run mandatory CI on the FINAL commit of the complete series, not intermediate
commits with intentionally incomplete version/dependency alignment.

## 1. fix: preserve HAI and CORE-SG scientific pipeline

- `mustache/core/batch.py`
- `mustache/core/clustering.py`
- `mustache/core/hai.py`
- `mustache/core/validation.py`

## 2. fix: clarify representatives and restore web project state

- `mustache/core/storage.py`
- `mustache/routes.py`
- `mustache/static/css/main.css`
- `mustache/static/js/main.js`
- `mustache/templates/base.html`
- `mustache/templates/dashboard.html`
- `mustache/templates/datasets.html`
- `mustache/templates/home.html`
- `mustache/templates/index.html`
- `mustache/templates/settings.html`

## 3. test: cover scientific behavior, persistence and release gates

- `tests/conftest.py`
- `tests/test_api_routes.py`
- `tests/test_release_metadata.py`
- `tests/test_release_promotion.py`
- `tests/test_scientific_review.py`

## 4. docs: clarify CORE-SG scope and English user guidance

- `benchmark.py`
- `docs/auditoria_entrega_pibic.md`
- `docs/benchmark_report.md`
- `docs/benchmark_report_canonical_hdbscan.md`
- `docs/final_audit_2026-09-27.md`
- `docs/final_summary_2026-09-27.md`
- `docs/guia_documentacao.md`
- `docs/index.md`
- `docs/reproducao.md`
- `docs/technical_review_2026-09-26.md`
- `examples/mustache_quickstart.ipynb`
- `examples/rc_minimal.py`
- `mkdocs.yml`
- `scripts/benchmark_coresg_vs_hdbscan.py`
- `scripts/benchmark_coresg_vs_hdbscan_canonical.py`

## 5. build: qualify Windows/Linux cp311 RC and release metadata

- `.github/workflows/ci.yml`
- `.github/workflows/docs.yml`
- `.github/workflows/release-testpypi.yml`
- `.github/workflows/release.yml`
- `AUTHORS.md`
- `AUTHORSHIP_APPROVAL_REQUIRED.md`
- `CHANGELOG.md`
- `CITATION.cff`
- `COMMIT_PLAN.md`
- `DATASETS.md`
- `MANIFEST.in`
- `README.md`
- `RELEASE_NOTES.md`
- `SECURITY_AUDIT_2026-09-27.md`
- `docs/rc_preparation.md`
- `docs/relatorio_empacotamento_wheels_e_testpypi.md`
- `mustache/__init__.py`
- `mustache/cli.py`
- `pyproject.toml`
- `release_candidate_readiness_2026-09-27.md`
- `requirements/README.md`
- `requirements/build-win-py311.txt`
- `requirements/runtime-win-py311.txt`
- `scripts/build_coresg_cython.ps1`
- `scripts/check_artifacts.py`
- `scripts/collect_release_artifacts.py`
- `scripts/qualify_artifacts.py`
- `scripts/rc_smoke.py`
- `scripts/rc_cli_smoke.py`
- `scripts/validate_promotion.py`
- `scripts/verify_web_ui.cjs`
- `testpypi_readiness_2026-09-27.md`

## Coordination before any remote write

Obtain owner approval of repository manuscript/privacy/license findings in
`SECURITY_AUDIT_2026-09-27.md`. Publication additionally needs authorship approval.
After explicit commit/push authorization, prepare CORE-SG first, record its final
immutable SHA, and qualify MustaCHE against that SHA on Windows/Linux. Record
both successful CI run IDs; create version tags only after separate authorization.
MacOS qualification is outside this RC; do not expand Python/platform claims
from workflow configuration alone. Recheck this inventory if any file changes.
