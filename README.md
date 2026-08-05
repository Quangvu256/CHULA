# ISO 19650 RDF Knowledge Graph & SHACL Audit Engine

A machine-verified W3C Semantic Web knowledge graph of the **complete ISO 19650 series** (Parts 1, 2, 3, 4, 5, 6), integrated with **Protégé Desktop**, a **Predictive Maintenance (PdM) use case**, and an **IFC + SHACL readiness checker** that audits BIM models against W3C SHACL shape constraints - the groundwork for a Cognitive Digital Twin (CDT).

**388 nodes / 1,094 relationships (12,418 RDF Triples)**, every entity carrying clause-level provenance into the standards. Backend is Python 3.10+ (`rdflib`, `pyshacl`, `SPARQLWrapper`), database is **Apache Jena Fuseki 5.0.0**, ontology editor is **Stanford Protégé Desktop**, and frontend is Angular.

```
┌──────────────────────────────────────────────────┐
│        Protégé Desktop Ontology Editor           │
│  (TBox Schema Management: iso19650_schema.ttl)   │
└────────────────────────┬─────────────────────────┘
                         │
                         ▼
ISO 19650 JSONs ──(export_rdf.py)──▶ [RDF Turtle (.ttl)] ──▶ [Apache Jena Fuseki]
                                            │                         │
                                            ▼                         ▼
                                   [PySHACL Engine] ◀───────── [SPARQL REST API]
                                            │                         │
                                            ▼                         ▼
                                   [IFC Audit Report]         [Angular Web UI]
```

## Quick start (Docker)

> **Data files first.** The six `iso19650-*_extraction*.json` files are ISO-derived and are **not in git**. Place them in `data/` before building. The tools generate RDF Turtle files (`iso19650_instances.ttl` and `iso19650_kg_unified.ttl`) dynamically.

```bash
cp .env.example .env
docker compose up -d --build
```

| Service | URL | What it is |
|---|---|---|
| Web UI | http://localhost:8000 | IFC checker - Requirements & why - Graph explorer |
| Jena Fuseki SPARQL | http://localhost:3030 | W3C SPARQL Endpoint & Query Console |

Export RDF Turtle graph, load into Fuseki & verify:

```bash
python3 backend/graphdb/export_rdf.py
python3 backend/graphdb/load_fuseki.py
```

Output: `data/generated/iso19650_instances.ttl` (ABox) & `data/generated/iso19650_kg_unified.ttl` (Unified TBox+ABox).

## Quick start (bare metal)

Requires Python >= 3.10 with RDF & SHACL dependencies installed:

```bash
pip install rdflib pyshacl SPARQLWrapper

# 1. Export RDF Turtle graph from original JSON files
python3 backend/graphdb/export_rdf.py

# 2. Load RDF Graph into Apache Jena Fuseki
python3 backend/graphdb/load_fuseki.py

# 3. Run SHACL & SPARQL Quality Gates evaluation
python3 backend/gates/evaluate_kg_shacl.py

# 4. Launch Web UI server
python3 backend/api/serve.py 8000
```

`poppler-utils` (`pdftotext`) is needed only if extracting text from source PDFs.

## Protégé Desktop Integration

1. Launch **Protégé Desktop 5.5+**.
2. Open TBox Schema: `data/ontology/iso19650_schema.ttl`
3. Or open Unified Knowledge Graph: `data/generated/iso19650_kg_unified.ttl`
4. Run **HermiT Reasoner** (`Reasoner -> HermiT -> Start Reasoner`) to verify ontology consistency and class hierarchy.

## Repository layout

| Path | Contents |
|---|---|
| `frontend/` | Angular app (5 tabs: IFC checker, requirements, graph explorer, method EN/VI, policies). Built bundle is served by backend. |
| `backend/` | Python backend: `serve.py` (REST API + static host), `export_rdf.py` (RDF Turtle exporter), `evaluate_kg_shacl.py` (E1-E5 quality gates via RDF/PySHACL), `check_ifc_shacl.py` (SHACL IFC audit CLI), `gen_pdm_spec.py`. |
| `data/` | Knowledge graph source JSONs: `iso19650-*_extraction*.json` (**Read-Only Input**). |
| `data/ontology/` | `iso19650_schema.ttl` - W3C OWL2 TBox Schema for Stanford Protégé Desktop. |
| `data/shapes/` | `pdm_ifc_shapes.ttl` - W3C SHACL Shapes definition for 13 quality gate and IFC rules. |
| `data/generated/` | Generated RDF Turtle files (`iso19650_instances.ttl`, `iso19650_kg_unified.ttl`) and evaluation reports. |
| `docs/` | Method documents: extraction protocol, conflict findings, evaluation reports. |

## Development & Toolchain

```bash
# Export RDF Turtle ABox & Unified Graph
python3 backend/graphdb/export_rdf.py

# Evaluate Quality Gates E1-E5 via RDFLib + PySHACL
python3 backend/gates/evaluate_kg_shacl.py

# Audit an IFC model against SHACL constraints
python3 backend/audit/check_ifc_shacl.py model.ifc --json report.json

# Launch API + built Angular frontend
python3 backend/api/serve.py 8000

# Frontend hot reload (terminal 2)
cd frontend && npm install && npx ng serve --proxy-config proxy.conf.json
```

## Quality Gates Verification

Every release is verified against five machine-enforced gates (`python3 backend/gates/evaluate_kg_shacl.py`):

| Gate | Description / Method | Status |
|---|---|---|
| **E1 Structural Integrity** | 388/388 nodes, 12,418 triples loaded into RDF Graph | `PASS` |
| **E2 Definition Fidelity** | 338 concepts verified with complete non-empty verbatim definitions | `PASS` |
| **E3 Reference Validity** | 1,482 nodes/statements mapped with exact standard & clause provenance | `PASS` |
| **E4 Traversability** | 360 nodes connected with active relational edges in graph component | `PASS` |
| **E5 SHACL Conformance** | Graph satisfies all W3C SHACL structural and provenance constraints | `PASS` |

## Web UI Features

- **Check IFC** - Drag-drop BIM IFC models, SHACL shape constraint audit, PASS/FAIL per rule, CDT-READY verdict.
- **Requirements & Why** - ISO 19650 requirements mapped to PdM lifecycle steps and cited RDF graph nodes.
- **Explore Graph** - Interactive visualization of the 388 nodes / 1,094 edges with node detail cards and part filters.
- **Method & Accuracy** - Live Quality Gate statistics served directly from PySHACL evaluation harness.
- **Policies & Privacy** - Local-only model processing, copyright compliance, and normative conflict governance.

## Licensing and Data Provenance

- **The ISO/BSI standards are copyrighted and are NOT distributed** with this repository.
- **The extraction JSONs remain untouched in `data/`** as read-only inputs.
- All ontology files (`.ttl`), SHACL shapes (`pdm_ifc_shapes.ttl`), and tooling code are original research work of this project.

## Research Context

Built as a research project (Chulalongkorn University) on W3C RDF & SHACL knowledge graph extraction of construction-information standards for Predictive Maintenance on Cognitive Digital Twins (CDT).
