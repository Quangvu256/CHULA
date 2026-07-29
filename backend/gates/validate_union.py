#!/usr/bin/env python3
"""Validate the union of the ISO 19650 extraction files.

Fails loudly on anything that would silently corrupt the merged Neo4j graph:
duplicate ids, duplicate names, dangling relationship endpoints, unknown
relationship types or labels, non-ASCII bytes, self-loops, exact duplicate edges.
"""
import json, os, sys, collections, unicodedata
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

FILES = ["data/iso19650-1_extraction_v4.json", "data/iso19650-2_extraction_v1.json",
         "data/iso19650-3_extraction_v1.2.json", "data/iso19650-4_extraction_v1.json", "data/iso19650-5_extraction_v1.json",
         "data/iso19650-6_extraction_v2.json"]

ALLOWED_TYPES = {  # Part 1 set + {REFINES, PRECEDES, LINKED_TO} from Part 3
    "AGGREGATED_INTO", "ALLOCATED_TO", "APPLIES_TO", "APPOINTS", "ASSIGNED_TO",
    "CONTRIBUTES_TO", "CORRESPONDS_TO", "DERIVED_FROM", "DESCRIBES", "DEVELOPED_INTO",
    "ENABLES", "ESTABLISHES", "GOVERNS", "LEADS", "MEMBER_OF", "PART_OF", "RECORDED_IN",
    "RESPONDS_TO", "RESPONSIBLE_FOR", "RESULTS_IN", "SERVES_PURPOSE", "SPECIFIED_IN",
    "STAGE_OF", "SUBTYPE_OF", "SUPPORTS", "TRANSITIONS_TO", "VIEWED_FROM",
    "REFINES", "PRECEDES", "LINKED_TO"}
ALLOWED_LABELS = {"Concept", "Purpose", "Principle", "State", "Perspective", "Function", "Activity"}

data = {f: json.load(open(f)) for f in FILES}
fail = []

ids, names = collections.defaultdict(list), collections.defaultdict(list)
for f, d in data.items():
    for n in d["nodes"]:
        ids[n["id"]].append(f)
        names[n["name"].strip().lower()].append((f, n["id"]))
        if n["label"] not in ALLOWED_LABELS:
            fail.append(f"unknown label {n['label']!r} on {n['id']} ({f})")
        for k in ("id", "label", "name", "definition", "provenance"):
            if not n.get(k):
                fail.append(f"missing {k} on node {n.get('id')} ({f})")

for i, fs in ids.items():
    if len(fs) > 1:
        fail.append(f"duplicate id {i} in {fs}")
for nm, v in names.items():
    if len(v) > 1:
        fail.append(f"duplicate name {nm!r} in {v}")

seen_edges = collections.Counter()
for f, d in data.items():
    for r in d["relationships"]:
        for e in (r["from"], r["to"]):
            if e not in ids:
                fail.append(f"dangling endpoint {e} in {f}")
        if r["type"] not in ALLOWED_TYPES:
            fail.append(f"new relationship type {r['type']} in {f}")
        if r["from"] == r["to"]:
            fail.append(f"self-loop on {r['from']} in {f}")
        if not r.get("provenance", {}).get("clause"):
            fail.append(f"edge without clause: {r['from']}->{r['to']} ({f})")
        seen_edges[(f, r["from"], r["type"], r["to"])] += 1
# Duplicates ACROSS files are deliberate: the same relationship asserted by two
# standards, each carrying its own provenance. Only a repeat inside one file is a bug.
for k, v in seen_edges.items():
    if v > 1:
        fail.append(f"duplicate edge x{v} within {k[0]}: {k[1:]}")

# ASCII / language check (uppercase-accented-safe: scan every codepoint)
for f, d in data.items():
    blob = json.dumps(d, ensure_ascii=False)
    bad = sorted({c for c in blob if ord(c) > 127})
    if bad:
        fail.append(f"non-ASCII in {f}: " +
                    ", ".join(f"U+{ord(c):04X} {unicodedata.name(c, '?')}" for c in bad[:12]))

n_nodes = sum(len(d["nodes"]) for d in data.values())
n_rels = sum(len(d["relationships"]) for d in data.values())
print(f"union: {n_nodes} nodes / {n_rels} relationships across {len(FILES)} files")
for f, d in data.items():
    print(f"  {f:34s} {len(d['nodes']):3d} nodes  {len(d['relationships']):3d} rels")

if fail:
    print("\nFAILURES:")
    for x in fail:
        print("  -", x)
    sys.exit(1)
print("\nOK: no duplicate ids/names, no dangling endpoints, no new types/labels, pure ASCII")
