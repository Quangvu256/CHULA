# ISO 19650 Knowledge Graph for Predictive Maintenance

A machine-verified knowledge graph of the **complete ISO 19650 series** (Parts 1,
2, 3, 4, 5, 6), a **Predictive Maintenance (PdM) use case** derived from it, and
an **IFC readiness checker** that audits BIM models against use-case
requirements generated from the graph - the groundwork for a Cognitive Digital
Twin.

**388 nodes / 1,094 relationships**, every one carrying clause-level provenance
into the standards. Backend is dependency-free Python (standard library only);
frontend is Angular.

```
ISO 19650 PDFs ──extraction protocol──▶ 6 extraction JSONs (the KG)
                                             │
                 ┌───────────────┬───────────┼──────────────┐
                 ▼               ▼           ▼              ▼
          Neo4j (Cypher    PdM use case   13 IFC        web UI: checker,
          export + load)   (in-graph)     requirements  requirements, graph
                                             │           explorer
                                             ▼
                                      IFC model audit ──▶ CDT-READY /
                                                          CONDITIONAL /
                                                          NOT READY
```

## Quick start (Docker)

> **Data files first.** The six `iso19650-*_extraction*.json` files and the
> generated `data/generated/load_iso19650_kg.cypher` are ISO-derived and are **not in
> git**. Get them from the project team (or rebuild per
> `docs/extraction_protocol.md` from licensed PDFs) and place them in the repo
> root before building - the tools fail fast with a clear error if they are
> missing.

```bash
cp .env.example .env          # then edit the Neo4j password
docker compose up -d --build
```

| Service | URL | What it is |
|---|---|---|
| Web UI | http://localhost:8000 | IFC checker - Requirements & why - Graph explorer |
| Neo4j Browser | http://localhost:7474 | Cypher access to the same graph |

Load the knowledge graph into Neo4j (one-off; idempotent - safe to re-run):

```bash
docker compose exec neo4j cypher-shell -u neo4j -p '<your-password>' \
  -f /import/load_iso19650_kg.cypher
```

Verify: `MATCH (n:Iso19650) RETURN count(n)` must return **388**.

## Quick start (bare metal)

Requires Python >= 3.9. No `pip install` - everything is standard library.

```bash
python3 backend/serve.py            # web UI on http://localhost:8000
python3 backend/check_ifc_pdm.py model.ifc --json report.json   # CLI audit
```

`pdftotext`/`pdftoppm` (poppler) are needed only by the tools that read the
source PDFs - see the licensing note below. macOS: `brew install poppler`.

## Repository layout

| Path | Contents |
|---|---|
| `frontend/` | Angular app (5 tabs: IFC checker, requirements, graph explorer, method & accuracy EN/VI, policies). Built bundle is served by the backend. |
| `backend/` | Python, stdlib-only: `serve.py` (REST API + static host), `check_ifc_pdm.py` (audit engine + CLI), `gen_pdm_spec.py`, `evaluate_kg.py` + gates, `draft_extractor.py`, `export_neo4j.py`, `pdm_competency.cypher`. |
| `data/` | The knowledge graph: `iso19650-*_extraction*.json`, one per standard. **Not committed** (ISO-derived) - obtain from the project team, place here. |
| `data/generated/` | Machine-generated artifacts: the 13-requirement spec, evaluation metrics, the Neo4j Cypher export (Cypher not committed). |
| `docs/` | Method documents: extraction protocol, conflict findings, evaluation report, use-case spec. |
| `1. ISO 19650 Series/` | **Not in the repo/image** - your licensed PDFs go here (see Licensing). |

## Development

```bash
# Backend (terminal 1) - no pip install, Python >= 3.9
python3 backend/serve.py                  # API + built frontend on :8000

# Frontend dev loop (terminal 2) - hot reload on :4200, /api proxied to :8000
cd frontend && npm install
npx ng serve --proxy-config proxy.conf.json

# Production build of the frontend (then backend serves it on :8000)
cd frontend && npx ng build
```

## The toolchain

```bash
# Audit an IFC model against the PdM requirements
python3 backend/check_ifc_pdm.py model.ifc            # exit 0 = CDT-READY, 2 otherwise

# Regenerate the requirements after any change to the KG
python3 backend/gen_pdm_spec.py

# Re-export and (re)load Neo4j after any change to the KG
python3 backend/export_neo4j.py
docker compose exec neo4j cypher-shell -u neo4j -p '<pw>' -f /import/load_iso19650_kg.cypher

# Run the full evaluation (needs the source PDFs on the host)
python3 backend/evaluate_kg.py                        # writes docs/evaluation_report.md

# First draft of a NEW standard, then curate per docs/extraction_protocol.md
python3 backend/draft_extractor.py path/to/standard.pdf "ISO XXXXX" --out draft.json
python3 backend/draft_extractor.py --benchmark        # score the generator vs gold
```

## Verification

Every merge must pass five machine-enforced gates
(`python3 backend/evaluate_kg.py`, exit 0). Current state:

| Gate | Checks | Result |
|---|---|---|
| E1 structural | duplicate ids/names, dangling endpoints, closed type/label sets, pure ASCII | PASS |
| E2 fidelity | every Clause-3 definition verbatim against its source PDF | 61 verbatim + 1 near / 62, 0 failures |
| E3 references | all provenance clause citations resolve in their standard | 1,486 / 1,486 |
| E4 traversability | 0 orphans, 1 component, 16-step PdM spine, high-PdM reachability | 16/16 spine, 196/196 |
| E5 coverage | source terms represented in the union | 67/67 |

The IFC checker itself has normative standing: ISO 19650-4:2022, 3.2.3 Note 3
allows an information reviewer to be *"an artificial intelligence agent or an
automated rules-based process"*, and clauses 7.2/7.6 make schema-conformance
and checklist-driven completeness checks part of the exchange review. The
generated spec records this under `normative_basis_for_automated_checking`.

## Web UI

- **Check IFC** - drag-drop a model, per-check PASS/FAIL with clause citations,
  verdict (CDT-READY / CONDITIONAL / NOT READY), report download / print.
- **Requirements & why** - each requirement with the PdM-loop step it serves,
  what breaks without it, what the checker actually probes, and its cited graph
  nodes tagged normative/informative/mixed.
- **Explore graph** - presets (PdM use case / high-PdM / everything), search,
  per-part filters, focus mode, fullscreen with floating node-detail card.
  Deterministic layout: the same filter always produces the same picture.
- **Method & accuracy** - animated PDF-to-graph pipeline and the live gate
  numbers (served from the last `evaluate_kg.py` run), plus the measured
  machine-alone ceiling from the extractor benchmark.
- **Policies & privacy** - local-only processing of uploaded models, standards
  copyright, personal data in H&S records, and the proposed governance
  defaults for the two detected normative conflicts.

## Contributing a new standard

Follow `docs/extraction_protocol.md`: machine first draft -> curation (tables,
figures from page images, annex lists, modality, cross-part reuse) -> the five
gates -> re-export -> reload. Part 4 was added exactly this way; the gates
passed on the first run.

## Licensing and data provenance

- **The ISO/BSI standards are copyrighted and are NOT distributed** with this
  repository or image (`.gitignore`/`.dockerignore` exclude
  `1. ISO 19650 Series/`). Place your own licensed copies there; the tools that
  need them (`evaluate_kg.py`, `draft_extractor.py`) run on the host.
- **The extraction JSONs and the Cypher export are not committed either**
  (`iso19650-*_extraction*.json`, `data/generated/load_iso19650_kg.cypher`): they contain
  verbatim definitions derived from the standards, produced for research
  purposes, and are shared within the project team only. The same applies to
  `data/generated/pdm_ifc_requirements.json` sources, which quote cited definitions - it
  is regenerable from the JSONs via `gen_pdm_spec.py`.
- Everything else - the method, tooling, generated requirements, and graph
  structure - is original work of this project.

## Research context

Built as a research project (Chulalongkorn University) on graph-based
extraction of construction-information standards for Predictive Maintenance on
Cognitive Digital Twins. Notable results: machine-detected normative conflicts
between ISO 19650-5 and -6 (`docs/conflict_findings.md`); a measured ceiling for
purely-programmatic extraction (term precision 97-100%, but 6-40% overall node
recall - the gap is table/figure/annex/interpretive content), which motivates
the hybrid extract-then-gate method.
