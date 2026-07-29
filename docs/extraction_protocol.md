# ISO 19650 extraction protocol

The extraction step is analyst/LLM judgment and is not a deterministic program.
Reproducibility is therefore established the way systematic reviews establish it:
a fixed protocol, machine-enforced acceptance gates, and a full audit trail -
two extractions that both pass every gate may differ in wording, but not in
structure, provenance, or fidelity.

## Inputs

One source PDF per part. Where two copies exist, keep both: the BSI copy of
Part 2 is complete but OCR-degraded ('B'->'8'), the ISO copy is clean text but
missing pages - their union is authoritative. Figures are read from page images
(`pdftoppm`), never assumed.

## Extraction rules (fixed conventions)

1. **Reuse-first.** A concept already present in ANY earlier file gets no new
   node - only a relationship pointing at the original id, with fresh
   `provenance {standard, clause}`. A node whose definition belongs to another
   standard carries `definition_provenance`.
2. **Ids and names.** `term_<snake_case>`; specialized prefixes (`state_`,
   `purpose_`, `stage_`, `field_`, `status_`, `grade_`, `activity_*[_delivery]`)
   instead of new labels. `name` globally unique across the union;
   same-name-different-meaning takes a disambiguating suffix.
3. **Closed vocabularies.** No relationship type outside Part 1's set plus
   {REFINES, PRECEDES, LINKED_TO}; no label outside Part 1's set plus Activity.
4. **Provenance on everything.** Every node and every edge carries
   {standard, clause} down to the lettered item ('5.4.3 c) 3)').
5. **Modality is data.** Normative vs informative vs mixed is recorded
   (`assertion_status` / `source_type`), never inferred by the reader.
6. **Interpretation is quarantined.** Anything not literally in a standard uses
   `provenance.standard = "USE-CASE EXTENSION"` with a clause of the form
   'mapped from ISO 19650-x <clause>...', so the standards-only graph is
   recoverable by one filter.
7. **English-only, pure ASCII.** Verified per codepoint, not by regex heuristics.
8. **Definitions verbatim.** The only permitted transformation is removal of
   inline cross-reference numbers '(3.3.1)'. Enrichment beyond the cited clause
   is forbidden; content merged from a second clause must cite it.
9. **Names may be coined** (noun-phrase labels for concepts the standard
   describes without naming) but definitions may not be.

## Acceptance gates (machine-enforced, one command each)

| Gate | Tool | Must hold |
|---|---|---|
| G1 structure | `backend/gates/validate_union.py` | 0 duplicate ids/names, 0 dangling endpoints, closed type/label sets, ASCII |
| G2 fidelity | `backend/gates/evaluate_kg.py` (E2) | every Clause-3 definition verbatim vs PDF |
| G3 references | `backend/gates/evaluate_kg.py` (E3) | every provenance clause resolves in its standard |
| G4 traversability | `backend/gates/check_pdm_paths.py` | 0 orphans, 1 component, PdM spine intact, high-PdM reachable |
| G5 coverage | `backend/gates/evaluate_kg.py` (E5) | source terms all represented in the union |

A change to any file re-runs all five gates; a merged graph is one that passes
all five. `backend/gates/evaluate_kg.py` emits the consolidated report
(`docs/evaluation_report.md`, `data/generated/evaluation_metrics.json`).

## Hybrid pipeline for new documents

1. `python3 backend/extraction/draft_extractor.py <pdf> "<standard>"` - deterministic first
   draft: Clause-3 terms (verbatim, provenance attached) + candidate edges from
   definition cross-references and trigger phrases. Everything `status: draft`.
2. Curation: resolve reuse against the union, add the structure the machine
   cannot see (tables, figures via page images, annex lists, modality,
   cross-part bridges), remove the `status` fields.
3. Gates G1-G5. Only then merge, re-export (`backend/graphdb/export_neo4j.py`), reload.

Benchmarked against the four hand-curated gold files (2026-07-29, v2 of the
generator, which adds machine modality tagging, registry-based reuse-first
resolution, and figure-legend extraction with PRECEDES chains): term precision
97-100%, term recall 97-100%, reuse resolution exercised (correct non-creation
of concepts the union already holds), figure-key candidates extracted but
largely paraphrase-named (actions vs the gold's noun phrases), and overall
node recall still only 6-40%. The shortfall that remains is the judgment
layer: table semantics, annex lists, interpretive bridging, relevance rating,
analytical notes. That measured ceiling is the reason the pipeline is hybrid
rather than automatic.
