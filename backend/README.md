# Backend

Dependency-free Python (standard library only), organized by function:

| Folder | Role | Entry points |
|---|---|---|
| `api/` | Web layer: REST endpoints (`/api/kg`, `/api/spec`, `/api/graph`, `/api/method`, `/api/check`) and static host for the built Angular bundle (SPA fallback) | `python3 backend/api/serve.py [port]` |
| `audit/` | The IFC readiness audit engine - the product. `run_check()` is imported by the API so CLI and web can never disagree | `python3 backend/audit/check_ifc_pdm.py model.ifc [--json out]` |
| `spec/` | Derives the 13 PdM requirements FROM the knowledge graph; deterministic, aborts if a cited node disappears | `python3 backend/spec/gen_pdm_spec.py` |
| `extraction/` | Machine first-draft generator for new standards, with a benchmark against the curated gold files | `python3 backend/extraction/draft_extractor.py <pdf> "<standard>"` / `--benchmark` |
| `gates/` | The five machine-enforced acceptance gates (E1-E5) and their harness; every merge must pass | `python3 backend/gates/evaluate_kg.py` |
| `graphdb/` | Self-contained Cypher export for Neo4j and the 10 competency queries | `python3 backend/graphdb/export_neo4j.py` |

Data flows: `extraction` (+ human curation per `docs/extraction_protocol.md`)
-> `data/*.json` -> `gates` -> `spec` + `graphdb` -> `audit`/`api`.
All scripts resolve paths from the repo root, so they can be run from anywhere.
