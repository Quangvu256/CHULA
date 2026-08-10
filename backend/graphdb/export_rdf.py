#!/usr/bin/env python3
"""Export the six ISO 19650 extraction JSON files to W3C RDF Turtle (.ttl) files.

Outputs:
  1. data/generated/iso19650_instances.ttl  - Instance data (ABox)
  2. data/generated/iso19650_kg_unified.ttl  - Combined Schema (TBox) + Instance Data (ABox)

Based entirely on the original 6 raw iso.json files without altering input data.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

import glob

def discover_kg_files_map():
    data_dir = "data"
    found = sorted(glob.glob(os.path.join(data_dir, "*extraction*.json")))
    active = [os.path.normpath(f).replace("\\", "/") for f in found if not f.endswith(".superseded")]
    out = {}
    for filepath in active:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                d = json.load(f)
                std = d.get("standard", "").split(":")[0].strip() or os.path.basename(filepath)
                out[filepath] = std
        except Exception:
            pass
    if out:
        return out
    return {
        "data/iso19650-1_extraction_v4.json": "ISO 19650-1",
        "data/iso19650-2_extraction_v1.json": "ISO 19650-2",
        "data/iso19650-3_extraction_v1.2.json": "ISO 19650-3",
        "data/iso19650-4_extraction_v1.json": "ISO 19650-4",
        "data/iso19650-5_extraction_v1.json": "ISO 19650-5",
        "data/iso19650-6_extraction_v2.json": "ISO 19650-6",
    }

FILES = discover_kg_files_map()

SCHEMA_PATH = "data/ontology/iso19650_schema.ttl"
OUT_ABOX = "data/generated/iso19650_instances.ttl"
OUT_UNIFIED = "data/generated/iso19650_kg_unified.ttl"


def ttl_str(s: str) -> str:
    """Format string as Turtle literal with multiline escaping."""
    if s is None:
        return '""'
    escaped = (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def safe_iri_suffix(s: str) -> str:
    """Ensure string is valid NCName for Turtle prefix usage."""
    cleaned = re.sub(r"[^\w\-.]", "_", s)
    if cleaned and cleaned[0].isdigit():
        cleaned = "_" + cleaned
    return cleaned


def main():
    os.makedirs("data/generated", exist_ok=True)

    header = [
        "@prefix iso: <http://example.org/iso19650#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        "# ISO 19650 Series - RDF ABox Instance Data",
        "# Generated automatically from raw JSON files - do not edit by hand.",
        "",
    ]

    lines = list(header)
    seen_ids = set()
    n_nodes = 0
    n_rels = 0

    # 1. Process Nodes
    for filepath, part in FILES.items():
        if not os.path.exists(filepath):
            print(f"Warning: file {filepath} not found.")
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        lines.append(f"\n# ---- {part} Nodes ({filepath}) ----\n")
        for node in data.get("nodes", []):
            nid = node["id"]
            if nid in seen_ids:
                raise ValueError(f"Duplicate node ID found across files: {nid}")
            seen_ids.add(nid)
            n_nodes += 1

            iri = f"iso:{safe_iri_suffix(nid)}"
            label = safe_iri_suffix(node.get("label", "IsoNode"))

            node_lines = [f"{iri} a iso:IsoNode, iso:{label} ;"]
            node_lines.append(f'    iso:nodeId {ttl_str(nid)} ;')
            node_lines.append(f'    iso:part {ttl_str(part)} ;')

            if "name" in node:
                node_lines.append(f'    rdfs:label {ttl_str(node["name"])} ;')
            if "definition" in node:
                node_lines.append(f'    iso:definition {ttl_str(node["definition"])} ;')
            if "term_no" in node:
                node_lines.append(f'    iso:termNo {ttl_str(str(node["term_no"]))} ;')
            if "source_type" in node:
                node_lines.append(f'    iso:sourceType {ttl_str(node["source_type"])} ;')
            if "pdm_relevance" in node:
                node_lines.append(f'    iso:pdmRelevance {ttl_str(node["pdm_relevance"])} ;')

            if "provenance" in node and isinstance(node["provenance"], dict):
                prov = node["provenance"]
                if "standard" in prov:
                    node_lines.append(f'    iso:provenanceStandard {ttl_str(prov["standard"])} ;')
                if "clause" in prov:
                    node_lines.append(f'    iso:provenanceClause {ttl_str(prov["clause"])} ;')

            if "definition_provenance" in node and isinstance(node["definition_provenance"], dict):
                dprov = node["definition_provenance"]
                if "standard" in dprov:
                    node_lines.append(f'    iso:defProvenanceStandard {ttl_str(dprov["standard"])} ;')
                if "clause" in dprov:
                    node_lines.append(f'    iso:defProvenanceClause {ttl_str(dprov["clause"])} ;')

            # Clean trailing semicolon
            node_lines[-1] = node_lines[-1][:-2] + " ."
            lines.extend(node_lines)

    # 2. Process Relationships
    for filepath, part in FILES.items():
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        lines.append(f"\n# ---- {part} Relationships ({filepath}) ----\n")
        for rel in data.get("relationships", []):
            from_id = rel["from"]
            to_id = rel["to"]
            rel_type = safe_iri_suffix(rel["type"])

            if from_id not in seen_ids or to_id not in seen_ids:
                raise ValueError(f"Dangling relationship endpoint in {filepath}: {rel}")

            from_iri = f"iso:{safe_iri_suffix(from_id)}"
            to_iri = f"iso:{safe_iri_suffix(to_id)}"
            pred_iri = f"iso:{rel_type}"

            # Direct Triple
            lines.append(f"{from_iri} {pred_iri} {to_iri} .")
            n_rels += 1

            # RDF Reification for Edge Provenance & Notes (Protégé / SPARQL compatible)
            prov = rel.get("provenance", {})
            note = rel.get("note", "")
            if prov or note:
                stmt_id = f"iso:rel_{n_rels}"
                lines.append(f"{stmt_id} a rdf:Statement ;")
                lines.append(f'    rdfs:label "reference number : {n_rels}" ;')
                lines.append(f"    rdf:subject {from_iri} ;")
                lines.append(f"    rdf:predicate {pred_iri} ;")
                lines.append(f"    rdf:object {to_iri} ;")
                if isinstance(prov, dict):
                    if "standard" in prov:
                        lines.append(f'    iso:provenanceStandard {ttl_str(prov["standard"])} ;')
                    if "clause" in prov:
                        lines.append(f'    iso:provenanceClause {ttl_str(prov["clause"])} ;')
                if note:
                    lines.append(f'    iso:relationshipNote {ttl_str(note)} ;')
                lines[-1] = lines[-1][:-2] + " ."

    # Write ABox
    abox_content = "\n".join(lines) + "\n"
    with open(OUT_ABOX, "w", encoding="utf-8") as f:
        f.write(abox_content)

    print(f"Wrote ABox ({OUT_ABOX}): {n_nodes} nodes, {n_rels} relationships.")

    # Generate Unified TTL (TBox + ABox)
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            tbox_content = f.read()
        unified_content = tbox_content + "\n\n# ==========================================\n# INSTANCE DATA (ABOX)\n# ==========================================\n\n" + abox_content
        with open(OUT_UNIFIED, "w", encoding="utf-8") as f:
            f.write(unified_content)
        print(f"Wrote Unified TTL ({OUT_UNIFIED}): Schema TBox + Instance ABox.")


if __name__ == "__main__":
    main()
