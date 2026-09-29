# Authorship decisions for this release candidate

The project owner has approved the modern software attribution for this RC.
No additional authorship decision is required before qualifying or publishing
this personal-fork release. This record does not decide future MIDAS ownership
or authorship of later releases.

MustaCHE 0.3.0rc3 is authored by Maylon Martins de Melo as modern software.
Murilo Coelho Naldi is credited for supervision, requirements and validation,
not automatically listed as a software coauthor. Historical authors remain
credited for the original work and implementation, not this reengineering.

| Role | Evidence / attribution | RC decision |
|---|---|---|
| Original scientific work | Antonio Cavalcante Araujo Neto, Mario A. Nascimento, Joerg Sander, Ricardo J. G. B. Campello; MustaCHE paper, PVLDB 2018 | Paper reference preserved; not modern software authors |
| Historical implementation | Source and original notices preserved under `legacy/`; paper authorship does not establish every implementation contributor | Historical credits preserved without inventing individual contributions |
| Modernization/reengineering | Maylon Martins de Melo; CORE-SG integration, reusable support corrections, interactive UI, persistence, tests and documentation | Sole named author of the modern software RC |
| Supervision | Murilo Coelho Naldi, IC advisor | Acknowledged for requirements, review and validation; not automatically software coauthor |
| Current contributions | Scientific fixes, metrics, representatives/reachability, qualification/packaging/CI and release documentation | Attributed to the modern project without a provisional collective author |

## CITATION.cff decision

- `authors`: Maylon Martins de Melo alone for the modern software release.
- `title`: modern software title, distinct from the original paper.
- `repository-code` / `url`: personal fork URLs for initial publication.
- `affiliation`: confirmed UFSCar department; MIDAS is described separately as
  a complementary research group in `AUTHORS.md`.
- `orcid`, `doi` and `date-released`: absent until independently verified or
  actually issued.

`version: 0.3.0rc3`, `type: software` and the historical paper references are
technical release/citation facts. The CORE-SG scientific paper remains a
separate reference. This file name is retained to avoid unnecessary package
metadata churn; the prior approval blocker is resolved for this RC.
