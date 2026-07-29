#!/usr/bin/env python3
"""Machine-generated FIRST DRAFT of an ISO 19650-style extraction - the automation
half of the hybrid pipeline. Deterministic, stdlib-only.

    python3 tmp/draft_extractor.py <pdf> "<standard name>" [--out draft.json]
    python3 tmp/draft_extractor.py --benchmark        # score the method against
                                                      # the hand-curated gold files

What it does (and honestly cannot do):
  DOES   - Clause-3 terms -> candidate nodes with verbatim definitions + provenance
         - '(3.x.y)' cross-references inside definitions -> candidate edges, with a
           suggested type when the genus-differentia pattern is unambiguous
         - trigger-phrase rules over body sentences mentioning two known terms
           ('shall establish' -> ESTABLISHES etc.), clause-attributed
  CANNOT - tables, figures, annex lists, modality nuance, cross-part reuse
           resolution, PdM relevance rating: exactly the content a curator adds.
Every output object carries status='draft'; nothing is merge-ready until it has
passed the gates in tmp/extraction_protocol.md.
"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evaluate_kg import text_of, parse_terms, clean, strip_xrefs, KG_FILES   # noqa: E402


def load_registry(exclude_standard=None):
    """name -> id map of every node already in the union (reuse-first, rule 1 of
    the protocol, machine-enforced). For benchmarking, the gold file's own
    standard is excluded so the resolver cannot cheat."""
    reg = {}
    for f in KG_FILES:
        if not os.path.exists(f):
            continue
        d = json.load(open(f))
        if exclude_standard and d["standard"].split(":")[0] == exclude_standard:
            continue
        for n in d["nodes"]:
            reg[clean(re.sub(r"\(.*?\)", "", n["name"]))] = n["id"]
    return reg


def figure_keys(txt):
    """Extract figure legend entries - they are text, unlike the artwork.
    Returns [(figure_no, key, text)] with key numeric or a single letter."""
    lines = txt.split("\n")
    cap = [(i, m.group(1)) for i, l in enumerate(lines)
           for m in [re.search(r"Figure\s+(\d+)\s*[-]", l)] if m]
    out = []
    for i, l in enumerate(lines):
        if not re.match(r"^\s*(Key|Activities)\s*$", l):
            continue
        j = i + 1
        while j < len(lines) and j < i + 40:
            m = re.match(r"^\s*(\d{1,2}|[A-Z])\s{2,}(\S.{3,90})$", lines[j])
            if m:
                # nearest caption within 45 lines either side
                near = min(cap, key=lambda c: abs(c[0] - i), default=(None, "?"))
                fig = near[1] if near[0] is not None and abs(near[0] - i) < 45 else "?"
                out.append((fig, m.group(1), m.group(2).strip()))
            elif lines[j].strip() and not re.match(r"^\s*(\d{1,2}|[A-Z])\s", lines[j]):
                break
            j += 1
    return out

TRIGGERS = [  # (phrase in sentence, relation type, direction subject->object)
    ("shall establish", "ESTABLISHES"),
    ("shall appoint", "APPOINTS"),
    ("responsible for", "RESPONSIBLE_FOR"),
    ("in accordance with", "SPECIFIED_IN"),
    ("part of", "PART_OF"),
    ("based on", "DERIVED_FROM"),
]


def snake(name):
    return "term_" + re.sub(r"[^a-z0-9]+", "_", clean(re.sub(r"\(.*?\)", "", name))).strip("_")


def draft_from_pdf(pdf, standard, registry=None):
    txt = text_of(pdf, {})
    raw_terms = parse_terms(txt)
    registry = registry if registry is not None else load_registry(standard)
    reused = []                      # concepts resolved against the union, not re-created
    # rebuild raw definitions WITH xref numbers for the edge pass
    nodes, edges = [], []
    no2id = {}
    for no, (name, definition) in raw_terms.items():
        key = clean(re.sub(r"\(.*?\)", "", name))
        if key in registry:          # protocol rule 1: reuse-first, machine-enforced
            no2id[no] = registry[key]
            reused.append({"term_no": no, "name": clean(name), "reuses": registry[key]})
            continue
        nid = snake(name)
        no2id[no] = nid
        nodes.append({"id": nid, "label": "Concept", "name": clean(name),
                      "definition": clean(strip_xrefs(definition)),
                      "provenance": {"standard": standard, "clause": no},
                      "term_no": no, "source_type": "terms_clause",
                      "modality": "normative",
                      "pdm_relevance": "unrated", "status": "draft"})
    # pass 1: cross-reference edges from definitions
    for no, (name, definition) in raw_terms.items():
        for m in re.finditer(r"\((\d+(?:\.\d+)+)\)", definition):
            ref = m.group(1)
            if ref not in no2id or no2id[ref] == no2id[no]:
                continue
            head = clean(strip_xrefs(definition))[:60]
            ref_name = clean(raw_terms[ref][0])
            suggested = ("SUBTYPE_OF" if head.startswith(ref_name) else "LINKED_TO")
            edges.append({"from": no2id[no], "to": no2id[ref], "type": suggested,
                          "provenance": {"standard": standard, "clause": no},
                          "status": "draft",
                          "note": "DRAFT: cross-reference in the definition; curate the type."})
    # pass 2: trigger phrases over body sentences
    names = sorted(((clean(n["name"]), n["id"]) for n in nodes),
                   key=lambda x: -len(x[0]))
    cur, hits = "?", set()
    for line in txt.split("\n"):
        h = re.match(r"^\s{0,10}(\d+(?:\.\d+)+)\s+[A-Z]", line)
        if h and "...." not in line:
            cur = h.group(1)
        low = clean(line)
        for phrase, rtype in TRIGGERS:
            if phrase not in low:
                continue
            present = [(low.find(nm), nid) for nm, nid in names if nm in low]
            if len({nid for _, nid in present}) < 2:
                continue
            present.sort()
            a, b = present[0][1], present[1][1]
            if a != b and (a, rtype, b) not in hits:
                hits.add((a, rtype, b))
                edges.append({"from": a, "to": b, "type": rtype,
                              "provenance": {"standard": standard, "clause": cur},
                              "status": "draft",
                              "note": f"DRAFT: trigger '{phrase}' in body sentence; verify direction and type."})
    # figure legends: emit key entries as candidate nodes (reuse-resolved), and
    # PRECEDES chains for numeric activity sequences
    have = {n["name"] for n in nodes}
    prev = {}
    for fig, key, text in figure_keys(txt):
        nm = clean(re.sub(r"\(.*?\)", "", text))
        if len(nm) < 4:
            continue
        rid = registry.get(nm)
        nid = rid or snake(nm)
        if not rid and nm not in have:
            have.add(nm)
            nodes.append({"id": nid, "label": "Concept", "name": nm,
                          "definition": f"figure key entry: {clean(text)}",
                          "provenance": {"standard": standard, "clause": f"Figure {fig} key {key}"},
                          "source_type": "figure_key", "modality": "normative",
                          "pdm_relevance": "unrated", "status": "draft"})
        elif rid:
            reused.append({"figure": fig, "key": key, "name": nm, "reuses": rid})
        if key.isdigit():
            k = int(key)
            if fig in prev and prev[fig][0] == k - 1 and prev[fig][1] != nid:
                edges.append({"from": prev[fig][1], "to": nid, "type": "PRECEDES",
                              "provenance": {"standard": standard,
                                             "clause": f"Figure {fig} keys {k-1}-{k}"},
                              "status": "draft",
                              "note": "DRAFT: consecutive numbered figure keys; verify the "
                                      "sequence is a flow, not a list."})
            prev[fig] = (k, nid)
    return {"standard": standard, "role_in_kg": "DRAFT - machine-generated, not curated",
            "extraction_notes": {"status": "draft", "generator": "tmp/draft_extractor.py",
                                 "caveats": "terms and definition cross-references only; "
                                 "tables, figures, annexes, modality and cross-part reuse "
                                 "require curation per tmp/extraction_protocol.md"},
            "reuse_resolved": reused,
            "nodes": nodes, "relationships": edges}


def benchmark():
    """Score the generator against the hand-curated gold files it did NOT help build."""
    GOLD = [("iso19650-1_extraction_v4.json", "1"),
            ("iso19650-4_extraction_v1.json", "4"),
            ("iso19650-5_extraction_v1.json", "5"),
            ("iso19650-6_extraction_v2.json", "6")]
    from evaluate_kg import pdf_for
    print(f"{'gold file':34s} {'node P':>7s} {'node R':>7s} {'termR':>6s} "
          f"{'edge R':>7s} {'typeOK':>7s}")
    for gf, part in GOLD:
        gold = json.load(open(gf))
        std = gold["standard"].split(":")[0]
        d = draft_from_pdf(pdf_for(part), std, registry=load_registry(exclude_standard=std))
        gnames = {clean(re.sub(r"\(.*?\)", "", n["name"])): n["id"] for n in gold["nodes"]}
        dterm = {clean(n["name"]): n["id"] for n in d["nodes"] if n.get("term_no")}
        dfig = {clean(n["name"]): n["id"] for n in d["nodes"] if n.get("source_type") == "figure_key"}
        # a reuse-resolution that names a concept the gold also knows counts as found
        dresolved = {r["name"]: r["reuses"] for r in d["reuse_resolved"]}
        dnames = {**dterm, **dresolved}
        matched = {dn: gnames[dn] for dn in dnames if dn in gnames}
        figmatched = {dn: gnames[dn] for dn in dfig if dn in gnames}
        # precision over CREATED nodes only: a reuse-resolution where gold also
        # declined to create a node is the correct action, not a miss
        createdP = {dn: dterm[dn] for dn in dterm}
        nodeP = (sum(1 for dn in createdP if dn in gnames) / len(createdP)) if createdP else 0
        nodeR = (len(matched) + len(figmatched)) / len(gnames)
        gterm = {clean(re.sub(r"\(.*?\)", "", n["name"])) for n in gold["nodes"] if n.get("term_no")}
        termR = sum(1 for t in gterm if t in dnames) / len(gterm) if gterm else 0
        dnames = {**dnames, **dfig}
        # edge endpoint-pair recall over gold edges whose BOTH endpoints were matched
        d2g = {dnames[dn]: gnames[dn] for dn in matched}
        dpairs = {frozenset((d2g.get(e["from"]), d2g.get(e["to"]))) for e in d["relationships"]}
        dtyped = {(d2g.get(e["from"]), e["type"], d2g.get(e["to"])) for e in d["relationships"]}
        matched_gold_ids = set(d2g.values())
        scoreable = [e for e in gold["relationships"]
                     if e["from"] in matched_gold_ids and e["to"] in matched_gold_ids]
        hit = [e for e in scoreable if frozenset((e["from"], e["to"])) in dpairs]
        typeok = sum(1 for e in hit if (e["from"], e["type"], e["to"]) in dtyped)
        edgeR = len(hit) / len(scoreable) if scoreable else 0
        print(f"{gf:34s} {nodeP:7.0%} {nodeR:7.0%} {termR:6.0%} "
              f"{edgeR:6.0%}* {typeok}/{len(hit):>4}")
        print(f"   draft: {len(dterm)} term nodes + {len(dfig)} figure-key candidates "
              f"({len(figmatched)} name-match gold; the rest are paraphrases, unscored), "
              f"{len(d['reuse_resolved'])} reuse-resolved, {len(d['relationships'])} cand. edges | "
              f"gold: {len(gold['nodes'])} nodes, {len(gold['relationships'])} edges")
    print("\n* edge recall is measured only over gold edges whose two endpoints the "
          "draft found at all - it answers 'of the relations between concepts the "
          "machine knows, how many did it propose', not 'of all knowledge in the "
          "standard'. The gap between the two IS the curation layer: tables, "
          "figures, annex lists, modality, cross-part reuse.")


if __name__ == "__main__":
    if "--benchmark" in sys.argv:
        benchmark()
    elif len(sys.argv) >= 3:
        out = (sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv
               else "draft_extraction.json")
        d = draft_from_pdf(sys.argv[1], sys.argv[2])
        json.dump(d, open(out, "w"), indent=2)
        print(f"wrote {out}: {len(d['nodes'])} draft nodes, "
              f"{len(d['relationships'])} candidate edges (status=draft)")
    else:
        sys.exit(__doc__)
