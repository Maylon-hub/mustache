# Pre-publication content and history audit — 2026-09-27

Scope: both local integration repositories and the four newly rebuilt Windows
RC artifacts. Read-only inspection; no credential validation, rotation, file
deletion, Git history rewriting or remote write was performed.

## A. Distributed artifacts

- MustaCHE wheel/sdist and CORE-SG Windows wheel/sdist: content checks passed.
- Gitleaks 8.30.1: zero alerts in extracted artifact text (98 MustaCHE text
  members, 99 CORE-SG text members). Generic Windows/macOS/Linux home-directory
  path patterns also produced zero matches across archive member contents.
- Native CORE-SG extensions are present; modern templates/static assets and
  citation/license/provenance/release files are present.
- No legacy tree, raw research datasets, manuscript PDF/TeX, benchmark outputs,
  caches, virtual environments, temporary build outputs or generated C files.
- This is evidence for **these Windows artifacts only**, not a security
  certification or inspection of a Linux wheel that does not yet exist.

## B. Current HEAD and working tree

| Repository | HEAD inventory | HEAD secret scan | Working-tree secret scan |
|---|---|---|---|
| MustaCHE | 16,425 files; 110.73 MB | No alerts | No alerts in audited snapshot |
| CORE-SG | 6,794 files; 109.63 MB | No alerts | No alerts in audited snapshot |

No tracked credential-container filenames (`.env`, `.pypirc`, private key
containers) were identified by the inventory. Environment-variable references
such as `GITHUB_TOKEN` are not embedded credential values.

Existing, preserved material still needs owner review before an institutional
push/transfer or unrestricted research-data reuse:

- MustaCHE: published article copies, the signed partial IC report and PIBIC
  manuscript/bibliography sources; 7 PDF/TeX/Bib files in HEAD. Confirm copyright,
  signatures/personal information and whether these documents should be public.
- CORE-SG: `paper/main.tex` and `paper/references.bib`; confirm unpublished
  manuscript status and institutional sharing permission.
- Home-directory patterns: 24 MustaCHE HEAD files / 23 files in the initial
  working-tree snapshot; 821 CORE-SG HEAD files / 821 working-tree files. These
  are candidate portability/privacy findings, not necessarily secrets. Most
  CORE-SG entries are stored benchmark provenance/output JSON.
- MustaCHE's historical sample CSVs lack verified origin/seed/license. CORE-SG
  research outputs and external dataset loaders do not imply blanket dataset
  redistribution rights. See both repositories' `DATASETS.md`.
- Large blobs still in HEAD: legacy MustaCHE `IHDBSCAN.jar` (24.36 MB); CORE-SG
  stored connectivity result CSVs (22.80, 11.83 and 5.92 MB). These are absent
  from the RC packages. No automatic removal or Git LFS conversion was made.

Package exclusion resolves distribution scope, **not** privacy/licensing of the
Git repository. The owner must approve the existing public-repository contents
before pushing these preparations or integrating into MIDAS.

## C. Historical Git objects

- Gitleaks scanned all reachable local refs/full history: MustaCHE 221 diff-bearing
  commits (~244 MB), CORE-SG 95 (~109 MB). Reachable commit totals are 243 and
  140 respectively; merge/empty commits explain the differing scan counts.
- MustaCHE: **18 generic API-key candidates**, all in historical Keen template
  demos (`keen-analytics.js`, demo dashboards and sample HTML). No corresponding
  alerts appeared in audited HEAD or working-tree snapshots; this does not
  establish whether a historical credential is still active.
- CORE-SG: zero secret alerts. Absence of alerts does not prove absence of secrets.
- Demo keys may have intentionally been public. Their ownership, permissions
  and current validity were **not tested**. An owner must determine whether
  revocation/rotation is needed before institutional history transfer; deleting
  a working-tree file cannot revoke a historical credential.
- Historical personal-path scan: 1,992 MustaCHE text blobs, 52 containing home
  paths (28 no longer in HEAD); 1,340 CORE-SG text blobs, 830 containing paths
  (9 no longer in HEAD). Findings contain only blob/path/line identifiers.
- Historical blobs >=5 MiB: 7 MustaCHE (1 still in HEAD), 3 CORE-SG (all in HEAD).
  This audit does not authorize republishing historical raw datasets or binaries.

## Method, evidence and limits

Tools: [Gitleaks 8.30.1](https://github.com/gitleaks/gitleaks) and Git object
inventory; tool-download SHA-256 was checked against upstream release checksums.
Secret JSON is fully redacted; summaries omit match/secret values. Local raw
inventories and logs live outside both checkouts in the dated
`rc-windows-linux-20260927` evidence directory and are not package contents.

Text scanning was limited to selected source/document/configuration extensions
and blobs <=5 MiB; binary/PDF content, image signatures, encrypted archives,
ignored/untracked private local files and unavailable remote refs are not
exhaustively inspected. Artifact path-pattern scanning also inspected binary
bytes, but does not constitute binary reverse engineering. No external secret
provider was contacted. Human manuscript/privacy/license review remains required.

## Required human decisions

1. Approve repository manuscript/signature/research-data sharing before push.
2. Determine whether historical Keen demo keys require owner-side revocation;
   do not print them or test their privileges in CI.
3. Confirm historical dataset rights before any MIDAS republication/reuse.
4. If history cleanup is desired, authorize an explicit, coordinated remediation
   plan with maintainers; this task did not rewrite history.

These repository/history decisions do not make macOS a publication blocker and
do not imply credential contamination of the inspected RC artifacts.
