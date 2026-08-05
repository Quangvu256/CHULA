# ISO 19650 & ISO 55000 Series RDF Knowledge Graph & SHACL Audit Engine

A machine-verified W3C Semantic Web knowledge graph covering **13 International Standards** across the **ISO 19650** series (Parts 1, 2, 3, 4, 5, 6), the **ISO 55000 Asset Management** family (ISO 55000, 55011, 55012, 55013, ISO/TS 55010), and the **ISO/IEC Digital Twin** standards (ISO/IEC 30173, ISO/IEC TR 30172).

Integrated with **Stanford Protégé Desktop**, **Apache Jena Fuseki 5.0+**, a **Predictive Maintenance (PdM)** use case specification, and an **IFC + SHACL readiness checker** that audits Building Information Modeling (BIM) models against W3C SHACL shape constraints — laying the groundwork for a **Cognitive Digital Twin (CDT)**.

**618 ISO Nodes / 1,535 Relational Edges (17,931 W3C RDF Triples)**, every entity carrying clause-level provenance into the international standards. Backend built on Python 3.10+ (`rdflib`, `pyshacl`, `SPARQLWrapper`), database powered by **Apache Jena Fuseki 5.0+**, ontology editor integrated with **Stanford Protégé Desktop 5.5+**, and frontend built with **Angular 19**.

```
┌──────────────────────────────────────────────────────────┐
│         Protégé Desktop Ontology Editor 5.5+             │
│   (TBox Schema Management: data/ontology/iso19650_schema.ttl) │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
13 ISO JSONs ──(export_rdf.py)──▶ [RDF Turtle (.ttl)] ──(PUT)──▶ [Apache Jena Fuseki :3030]
                                          │                                   │
                                          ▼                                   ▼
                                 [PySHACL Engine] ◀─────────────── [SPARQL REST API]
                                          │                                   │
                                          ▼                                   ▼
                                 [IFC Audit Report]               [Angular 19 Web UI :8000]
```

---

## 13 International Standards Covered

| Standard | Description | Scope in Graph |
|---|---|---|
| **ISO 19650-1:2018** | Concepts and principles for information management | 82 nodes / 103 rels |
| **ISO 19650-2:2018** | Delivery phase of the assets | 25 nodes / 150 rels |
| **ISO 19650-3:2020** | Operational phase of the assets | 85 nodes / 210 rels |
| **ISO 19650-4:2022** | Information exchange (Automated review criteria) | 22 nodes / 84 rels |
| **ISO 19650-5:2020** | Security-minded approach to information management | 84 nodes / 245 rels |
| **ISO 19650-6:2025** | Health and safety information management | 90 nodes / 302 rels |
| **ISO 55000:2024** | Asset management — Vocabulary, overview and principles | 44 nodes / 74 rels |
| **ISO 55011:2024** | Asset management — Government and public infrastructure | 21 nodes / 43 rels |
| **ISO 55012:2024** | Asset management — Enhancing asset management capabilities | 22 nodes / 45 rels |
| **ISO 55013:2024** | Asset management — Guidance on the management of data assets | 24 nodes / 59 rels |
| **ISO/TS 55010:2019** | Alignment of financial and non-financial functions in AM | 57 nodes / 113 rels |
| **ISO/IEC 30173:2023** | Digital Twin — Concepts and terminology | 40 nodes / 68 rels |
| **ISO/IEC TR 30172:2023** | Digital Twin — Use cases | 22 nodes / 39 rels |

---

## Quick Start (Docker)

> **Data files included.** The 13 `*extraction*.json` files in `data/` represent curated, machine-verified extractions of the ISO standards. The toolchain dynamically generates RDF Turtle files (`iso19650_instances.ttl` and `iso19650_kg_unified.ttl`).

```bash
# 1. Clone environment variables
cp .env.example .env

# 2. Build and launch Docker services
docker compose up -d --build
```

| Service | URL | Description |
|---|---|---|
| **Angular Web UI** | [http://localhost:8000](http://localhost:8000) | IFC Checker, Requirements & Why, Graph Explorer, Fuseki Monitoring |
| **Jena Fuseki SPARQL** | [http://localhost:3030](http://localhost:3030) | W3C SPARQL Query Endpoint & Dataset Admin Console |

To re-export RDF Turtle data and update Fuseki inside Docker:

```bash
python3 backend/graphdb/export_rdf.py
python3 backend/graphdb/load_fuseki.py
```

---

## Quick Start (Bare Metal)

Requires Python >= 3.10 and Node.js >= 20:

```bash
# Install Python dependencies
pip install rdflib pyshacl SPARQLWrapper

# 1. Validate union graph integrity across all 13 standards
python3 backend/gates/validate_union.py

# 2. Export RDF Turtle graph (ABox & Unified TBox+ABox)
python3 backend/graphdb/export_rdf.py

# 3. Load RDF Graph into Apache Jena Fuseki (HTTP PUT Overwrite)
python3 backend/graphdb/load_fuseki.py

# 4. Evaluate SHACL & SPARQL Quality Gates E1-E5
python3 backend/gates/evaluate_kg_shacl.py

# 5. Generate Predictive Maintenance IFC Specification
python3 backend/spec/gen_pdm_spec.py

# 6. Launch Web API & UI server
python3 backend/api/serve.py 8000
```

---

## Protégé Desktop Integration

1. Launch **Stanford Protégé Desktop 5.5+**.
2. Open TBox Schema: [data/ontology/iso19650_schema.ttl](file:///d:/BIMLab/CHULA/chuLA/data/ontology/iso19650_schema.ttl)
3. Or open Unified Knowledge Graph: [data/generated/iso19650_kg_unified.ttl](file:///d:/BIMLab/CHULA/chuLA/data/generated/iso19650_kg_unified.ttl)
4. Run **HermiT Reasoner** (`Reasoner -> HermiT -> Start Reasoner`) to verify ontology consistency, class hierarchies, and object property inferences.

---

## Quality Gates Verification

Every release is verified against five machine-enforced quality gates ([backend/gates/evaluate_kg_shacl.py](file:///d:/BIMLab/CHULA/chuLA/backend/gates/evaluate_kg_shacl.py)):

| Gate | Description / Verification Method | Status |
|---|---|---|
| **E1 Structural Integrity** | 618 nodes, 17,931 triples loaded into RDF Graph with zero dangling endpoints | `PASS` |
| **E2 Definition Fidelity** | 560 concepts verified verbatim against source ISO text (eliding inline cross-refs) | `PASS` |
| **E3 Reference Validity** | 2,153 nodes & statements mapped with exact standard and clause provenance | `PASS` |
| **E4 Traversability** | 519 nodes connected in active relational graph component with 16-step PdM spine | `PASS` |
| **E5 SHACL Conformance** | Graph satisfies all W3C SHACL shape constraints defined in `pdm_ifc_shapes.ttl` | `PASS` |

---

## Repository Layout

| Path | Description |
|---|---|
| [frontend/](file:///d:/BIMLab/CHULA/chuLA/frontend) | Angular 19 web application (5 tabs: Check IFC, Requirements & Why, Explore Graph, Fuseki Monitoring, Method & Accuracy, Policies). |
| [backend/api/](file:///d:/BIMLab/CHULA/chuLA/backend/api) | `serve.py` - FastAPI/Python REST API server and static host for built Angular UI. |
| [backend/graphdb/](file:///d:/BIMLab/CHULA/chuLA/backend/graphdb) | `export_rdf.py` (W3C Turtle exporter), `load_fuseki.py` (HTTP PUT Fuseki uploader), `export_neo4j.py` (Cypher exporter). |
| [backend/gates/](file:///d:/BIMLab/CHULA/chuLA/backend/gates) | `validate_union.py` (Structural validator), `evaluate_kg_shacl.py` (E1-E5 SHACL Quality Gates harness), `check_pdm_paths.py`. |
| [backend/audit/](file:///d:/BIMLab/CHULA/chuLA/backend/audit) | `check_ifc_pdm.py` (IFC SPF/STEP tokenizer & audit engine), `check_ifc_shacl.py` (SHACL IFC auditor CLI). |
| [backend/spec/](file:///d:/BIMLab/CHULA/chuLA/backend/spec) | `gen_pdm_spec.py` - Generates machine-readable requirement specification (`pdm_ifc_requirements.json`). |
| [data/](file:///d:/BIMLab/CHULA/chuLA/data) | Source extraction JSON files across 13 standards (`iso19650-*`, `iso-55000*`, `iso-ts-55010*`, `iso-iec*`). |
| [data/ontology/](file:///d:/BIMLab/CHULA/chuLA/data/ontology) | `iso19650_schema.ttl` - W3C OWL2 TBox Schema for Stanford Protégé Desktop. |
| [data/shapes/](file:///d:/BIMLab/CHULA/chuLA/data/shapes) | `pdm_ifc_shapes.ttl` - W3C SHACL Shapes definition for quality gates and IFC rules. |
| [data/generated/](file:///d:/BIMLab/CHULA/chuLA/data/generated) | Dynamic outputs: `iso19650_instances.ttl` (ABox), `iso19650_kg_unified.ttl` (Unified), `pdm_ifc_requirements.json`. |
| [docs/](file:///d:/BIMLab/CHULA/chuLA/docs) | `evaluation_shacl_report.md`, `onboarding_guide.md`, `pdm_use_case_spec.md`, `conflict_findings.md`. |

---

## Development & Toolchain

```bash
# Validate graph structure & detect any duplicate IDs across 13 standards
python3 backend/gates/validate_union.py

# Export RDF Turtle ABox & Unified Graph
python3 backend/graphdb/export_rdf.py

# Upload Unified Turtle to Fuseki dataset /iso19650 via HTTP PUT
python3 backend/graphdb/load_fuseki.py

# Evaluate Quality Gates E1-E5 via RDFLib + PySHACL
python3 backend/gates/evaluate_kg_shacl.py

# Audit an IFC model against SHACL constraints
python3 backend/audit/check_ifc_shacl.py model.ifc --json report.json

# Launch API & Angular Production Web UI
python3 backend/api/serve.py 8000

# Frontend hot reload (for UI development)
cd frontend
npm install
npx ng serve --proxy-config proxy.conf.json
```

---

## Web UI Features

- **Check IFC**: Drag & drop BIM IFC models (`.ifc`, `.ifcxml`), execute SHACL shape constraint audits, inspect rule-by-rule PASS/FAIL reports, and view Cognitive Digital Twin readiness verdicts (`CDT-READY`, `CONDITIONAL`, `NOT READY`).
- **Requirements & Why**: Interactive mapping of 13 Predictive Maintenance (PdM) rules derived from ISO 19650, linking each IFC property/class probe to its normative ISO clause and RDF graph node.
- **Explore Graph**: Visual search and navigation across 618 nodes and 1,535 relational edges with standard filters (ISO 19650, ISO 55000, ISO/IEC 30173), PdM relevance highlights, and clause provenance cards.
- **Fuseki Monitoring**: Real-time connection metrics to Apache Jena Fuseki SPARQL endpoint (`:3030`), live SPARQL console, and dataset graph statistics.
- **Method & Accuracy**: Real-time Quality Gate metrics (E1-E5) served straight from the PySHACL evaluation harness.
- **Policies & Privacy**: Local-only model parsing, copyright governance, and normative conflict resolution docs.

---

## Licensing & Data Provenance

- **ISO & BSI standards are copyrighted** and are NOT distributed in raw text format within this repository.
- The extraction JSON files in `data/` record structured concept nodes, verbatim clause-3 definitions, and relationship provenance under fair-use research guidelines.
- All ontology schemas (`.ttl`), SHACL shapes (`pdm_ifc_shapes.ttl`), Python backend tooling, and Angular Web UI code are original research contributions of this project.

---

## Research Context

Developed as a research project at **Chulalongkorn University (BIMLab)** on W3C RDF & SHACL knowledge graph extraction of construction-information standards for **Predictive Maintenance (PdM)** on **Cognitive Digital Twins (CDT)**.
