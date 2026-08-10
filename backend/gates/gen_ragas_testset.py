#!/usr/bin/env python3
"""Generate a RAGAS Golden Evaluation Testset from the 13 ISO Extraction JSON files.

Usage:
    python backend/gates/gen_ragas_testset.py
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT, "data")
OUT_JSON = os.path.join(DATA_DIR, "generated", "golden_testset_ragas.json")
OUT_JSON_ROOT = os.path.join(DATA_DIR, "golden_testset_from_json.json")

def main():
    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    # Filter out .superseded and generated golden_testset files
    json_files = [f for f in json_files if not f.endswith(".superseded") and "golden_testset" not in f]
    json_files.sort()

    print(f"Found {len(json_files)} active ISO extraction JSON files.")

    golden_testset = []
    seen_nodes = set()
    count = 0

    for file_path in json_files:
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load {filename}: {e}")
                continue
            
            if isinstance(data, list):
                nodes = data
            elif isinstance(data, dict):
                nodes = data.get("nodes", [])
            else:
                nodes = []
            file_count = 0
            for node in nodes:
                node_id = node.get("id") or node.get("node_id")
                if not node_id or node_id in seen_nodes:
                    continue
                
                name = node.get("name") or node.get("label") or node_id
                definition = node.get("definition", "")
                
                # Check nested provenance or flat standard/clause
                prov = node.get("provenance", {})
                std = prov.get("standard") or node.get("standard") or data.get("standard") or data.get("metadata", {}).get("standard") or "ISO Standard"
                clause = prov.get("clause") or node.get("clause") or node.get("term_no") or "Normative Clause"
                pdm_rel = node.get("pdm_relevance") or "medium"

                # Filter for non-empty meaningful definitions
                if definition and len(definition.strip()) > 5:
                    seen_nodes.add(node_id)
                    count += 1
                    file_count += 1
                    
                    test_case = {
                        "id": f"RAGAS-ISO-{count:03d}",
                        "node_id": node_id,
                        "question": f"Khái niệm '{name}' được định nghĩa như thế nào trong tiêu chuẩn {std} điều khoản {clause}?",
                        "ground_truth": f"Khái niệm '{name}' theo tiêu chuẩn {std} điều khoản {clause} được định nghĩa là: {definition}",
                        "retrieved_context": f"iso:{node_id} a iso:Concept ;\n  rdfs:label \"{name}\" ;\n  iso:provenanceStandard \"{std}\" ;\n  iso:provenanceClause \"{clause}\" ;\n  iso:definition \"{definition}\" ;\n  iso:pdmRelevance \"{pdm_rel}\" .",
                        "standard_citation": f"{std} Clause {clause}",
                        "pdm_relevance": pdm_rel
                    }
                    golden_testset.append(test_case)
            
            print(f"  - {filename}: Extracted {file_count} test cases.")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)

    with open(OUT_JSON, "w", encoding="utf-8") as out:
        json.dump(golden_testset, out, indent=2, ensure_ascii=False)

    with open(OUT_JSON_ROOT, "w", encoding="utf-8") as out:
        json.dump(golden_testset, out, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully generated {len(golden_testset)} Golden RAGAS Test Cases!")
    print(f"  - Saved to: {OUT_JSON}")
    print(f"  - Saved to: {OUT_JSON_ROOT}")

if __name__ == "__main__":
    main()
