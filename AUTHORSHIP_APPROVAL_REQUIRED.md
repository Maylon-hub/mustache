# Authorship approval required

Proposal for MustaCHE 0.3.0rc3; confirm with Maylon, Murilo and the affected
maintainers before software publication. This file records pending decisions;
it does not appoint institutional owners or rank contributions.

| Role | Evidence / attribution | Decision still required |
|---|---|---|
| Original scientific work | Antonio Cavalcante Araujo Neto, Mario A. Nascimento, Joerg Sander, Ricardo J. G. B. Campello; MustaCHE paper, PVLDB 2018 | Preserve paper citation; confirm spelling against the paper if changing it |
| Historical implementation | Source and original notices preserved under `legacy/`; paper authorship does not establish every implementation contributor | Identify any additional individual software credits from original records; do not infer them from the paper alone |
| Modernization/reengineering | Maylon Martins de Melo; CORE-SG integration, reusable support corrections, interactive UI, persistence, tests and English documentation | Confirm modern software author list and contribution wording |
| Supervision | Murilo Coelho Naldi, stated IC advisor | Confirm acknowledgement versus software authorship based on actual contributions; supervision alone is not software authorship |
| Current contributions | Consolidated scientific fixes, metrics, representatives/reachability, qualification/packaging/CI and release documentation | Confirm contributors and whether the provisional collective is appropriate; no automatic author ordering from commit counts |

## CITATION.cff fields requiring confirmation

- `authors`: Maylon's given/family-name split, complete list and order, and
  provisional `MustaCHE contributors` collective.
- `title`: proposed modern software title, distinct from the original paper.
- `message`: replace provisional wording only after approval is recorded.
- `repository-code` / `url`: current personal fork URLs; change only after an
  authorized institutional ownership decision.
- Any future `orcid`, `affiliation`, `doi` or `date-released`: currently absent;
  add only verified identifiers and the actual release/deposit date.

`version: 0.3.0rc3`, `type: software` and the historical paper references are
technical release/citation facts, not permission to decide institutional authorship.
The CORE-SG scientific paper remains a separate reference. No ORCID, new
affiliation or author order is invented here. Record the advisor/maintainer's
decision before TestPyPI publication, without requiring approval to run CI.
