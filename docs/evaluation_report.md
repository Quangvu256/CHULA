# ISO 19650 knowledge graph - evaluation report

Graph under evaluation: 388 nodes / 1094 relationships across 6 extraction files.

| Layer | Metric | Result |
|---|---|---|
| E1 structural integrity | duplicate ids/names, dangling endpoints, type/label closure, ASCII | PASS |
| E2 definition fidelity | Clause-3 definitions matched verbatim against source PDFs | 61 verbatim + 1 near (cross-ref elision) / 62, failures: 0 |
| E3 reference validity | provenance clause references resolved against PDF heading inventories | 1486/1486 |
| E4 traversability | orphans, connected components, PdM spine, high-PdM reachability | spine 16/16, high-PdM 196/196, PASS |
| E5 term coverage | source Clause-3 terms represented in the union graph | 67/67 (19650-1: 34/34, 19650-2: 7/7, 19650-3: 2/2, 19650-4: 4/4, 19650-5: 15/15, 19650-6: 5/5) |

Overall: ALL LAYERS PASS

Method notes: E2 tolerates exactly one transformation - removal of inline cross-reference numbers like '(3.3.1)' - and E2 'near' rows are artifacts of the PDF term parser (admitted-term lines merged into the definition), each manually reviewed on 2026-07-29. The term parser drops short admitted-term/abbreviation lines between the preferred term and its definition, per the ISO terms layout. Heading inventories accept table-of-contents entries as heading evidence (the BSI P2 body is OCR-degraded; its TOC is not). E3 resolves free-text attributions ('mapped from ISO 19650-x ...') against the named standard, so cross-standard citations are checked against the right document.
