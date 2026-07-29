#!/usr/bin/env python3
"""Check an IFC (STEP/SPF) model against the PdM use-case requirements.

Usage:  python3 backend/check_ifc_pdm.py <model.ifc> [--json out.json]

Reads data/generated/pdm_ifc_requirements.json (generated from the knowledge
graph by backend/gen_pdm_spec.py). Stdlib only - no ifcopenshell needed: presence/coverage
checks only require entity types, string attributes and the five binding
relationships (properties, containment, groups, classification), which a small
SPF tokenizer can index reliably.

ponytail: heuristic attribute positions (GlobalId = first string, Name/Tag =
any later non-empty string); upgrade to ifcopenshell if per-attribute fidelity
ever matters.
"""
import json, os, re, sys, collections

# ---------------------------------------------------------------- SPF parser
def parse_spf(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)          # strip comments
    m = re.search(r"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'", text)
    schema = (m.group(1).upper() if m else "UNKNOWN")
    ents = {}
    for m in re.finditer(r"#(\d+)\s*=\s*([A-Za-z0-9_]+)\s*\(", text):
        eid, etype = int(m.group(1)), m.group(2).upper()
        j, depth, instr, buf = m.end(), 1, False, []
        n = len(text)
        while j < n:
            c = text[j]
            if instr:
                if c == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        buf.append("''"); j += 2; continue
                    instr = False
            elif c == "'":
                instr = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            buf.append(c); j += 1
        args = "".join(buf)
        ents[eid] = {
            "type": etype,
            "refs": [int(x) for x in re.findall(r"#(\d+)", args)],
            "strs": [s.replace("''", "'") for s in re.findall(r"'((?:[^']|'')*)'", args)],
        }
    return schema, ents


def build_index(ents):
    ix = collections.defaultdict(list)              # type -> [ids]
    for i, e in ents.items():
        ix[e["type"]].append(i)

    def typed(i):
        return ents[i]["type"] if i in ents else "?"

    # element -> pset names, and pset name -> property names
    elem_psets = collections.defaultdict(set)
    pset_props = collections.defaultdict(set)
    for i in ix["IFCPROPERTYSET"]:
        name = (ents[i]["strs"][1] if len(ents[i]["strs"]) > 1 else
                (ents[i]["strs"][0] if ents[i]["strs"] else ""))
        for r in ents[i]["refs"]:
            if typed(r).startswith("IFCPROPERTY"):
                if ents[r]["strs"]:
                    pset_props[name].add(ents[r]["strs"][0])
        ents[i]["pset_name"] = name
    for i in ix["IFCRELDEFINESBYPROPERTIES"]:
        refs = [r for r in ents[i]["refs"] if typed(r) != "IFCOWNERHISTORY"]
        psets = [r for r in refs if typed(r) in ("IFCPROPERTYSET", "IFCELEMENTQUANTITY")]
        elems = [r for r in refs if r not in psets]
        for p in psets:
            for el in elems:
                elem_psets[el].add(ents[p].get("pset_name", ""))

    contained = set()                               # element ids inside spatial structure
    for i in ix["IFCRELCONTAINEDINSPATIALSTRUCTURE"] + ix["IFCRELAGGREGATES"]:
        for r in ents[i]["refs"]:
            if typed(r) != "IFCOWNERHISTORY":
                contained.add(r)

    grouped = set()                                 # element ids assigned to any group/system
    for i in ix["IFCRELASSIGNSTOGROUP"]:
        refs = [r for r in ents[i]["refs"] if typed(r) != "IFCOWNERHISTORY"]
        for r in refs:
            if not typed(r).startswith(("IFCSYSTEM", "IFCDISTRIBUTIONSYSTEM",
                                        "IFCBUILDINGSYSTEM", "IFCZONE", "IFCGROUP")):
                grouped.add(r)

    classified = set()                              # element ids with a classification ref
    for i in ix["IFCRELASSOCIATESCLASSIFICATION"]:
        for r in ents[i]["refs"]:
            if typed(r) not in ("IFCOWNERHISTORY", "IFCCLASSIFICATIONREFERENCE",
                                "IFCCLASSIFICATION"):
                classified.add(r)

    return dict(ix=ix, elem_psets=elem_psets, pset_props=pset_props,
                contained=contained, grouped=grouped, classified=classified)


# ---------------------------------------------------------------- evaluators
def equipment_ids(ix, entities):
    # spec lists IFC classes in camelCase for display; SPF stores them upper-case
    return [i for t in entities for i in ix.get(t.upper(), [])]


def evaluate(req, schema, ents, idx):
    p, ix = req["probe"], idx["ix"]
    k = p["kind"]
    if k == "entity_any":
        found = {t: len(ix[t.upper()]) for t in p["entities"] if ix.get(t.upper())}
        ok = bool(found)
        det = ", ".join(f"{t}x{c}" for t, c in found.items()) or "none found"
        pw = p.get("proxy_warn", "").upper()
        if not ok and pw and ix.get(pw):
            det += f" (only {p['proxy_warn']}x{len(ix[pw])} - untyped proxies)"
        return ok, det
    eq = equipment_ids(ix, p.get("entities", []))
    if k == "identifiers":
        if not eq:
            return False, "no equipment to identify"
        gids = [ents[i]["strs"][0] for i in eq if ents[i]["strs"]]
        named = [i for i in eq if any(s.strip() for s in ents[i]["strs"][1:])]
        dup = len(gids) - len(set(gids))
        ok = dup == 0 and len(named) / len(eq) >= p["min_named"]
        return ok, f"{len(eq)} equipment, GlobalId dup={dup}, named/tagged={len(named)}/{len(eq)}"
    if k == "containment":
        spatial = {t: len(ix[t.upper()]) for t in p["spatial"] if ix.get(t.upper())}
        if not spatial:
            return False, "no spatial structure at all"
        if not eq:
            return False, "spatial structure ok but no equipment"
        inn = sum(1 for i in eq if i in idx["contained"])
        ok = inn / len(eq) >= p["min_contained"]
        return ok, f"spatial={'/'.join(spatial)}, contained={inn}/{len(eq)}"
    if k == "system_assignment":
        systems = sum(len(ix[t.upper()]) for t in p["systems"] if ix.get(t.upper()))
        if not systems:
            return False, "no IfcSystem/IfcDistributionSystem"
        inn = sum(1 for i in eq if i in idx["grouped"])
        return inn > 0, f"systems={systems}, equipment assigned={inn}/{len(eq)}"
    if k == "classification":
        if not eq:
            return False, "no equipment"
        cls = sum(1 for i in eq if i in idx["classified"])
        return cls > 0, f"classified equipment={cls}/{len(eq)} " \
                        f"(IfcClassification x{len(ix.get('IFCCLASSIFICATION', []))})"
    if k == "pset_coverage":
        if not eq:
            return False, "no equipment"
        if "psets" in p:
            hit = [i for i in eq if any(ps in idx["elem_psets"].get(i, ())
                                        for ps in p["psets"])]
        else:
            pre, suf = p["psets_prefix_suffix"]
            hit = [i for i in eq if any(ps.startswith(pre) and ps.endswith(suf)
                                        for ps in idx["elem_psets"].get(i, ()))]
        ok = len(hit) / len(eq) >= p["min"]
        return ok, f"coverage {len(hit)}/{len(eq)} (need >= {p['min']:.0%})"
    if k == "pset_risk":
        col = ("ifc4_3" if "4X3" in schema else
               "ifc2x3" if "2X3" in schema else "ifc4_0")
        want = set(p["props_by_schema"][col])
        have = idx["pset_props"].get("Pset_Risk", set())
        if not have:
            return False, f"no Pset_Risk (schema {schema} -> expects {col} names)"
        return True, f"Pset_Risk with {len(have & want)}/{len(want)} {col} properties: " \
                     + ", ".join(sorted(have & want)[:6])
    if k == "property_name_contains":
        hits = [pr for props in idx["pset_props"].values() for pr in props
                if p["needle"].lower() in pr.lower()]
        return bool(hits), f"properties matching '{p['needle']}': {hits[:4] or 'none'}"
    if k == "pset_any":
        found = [ps for ps in p["psets"] if ps in idx["pset_props"]
                 or any(ps in v for v in idx["elem_psets"].values())]
        return bool(found), f"present: {found or 'none'}"
    raise ValueError(f"unknown probe kind {k}")


# ---------------------------------------------------------------- public API
SPEC_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data", "generated", "pdm_ifc_requirements.json")


def load_spec(path=SPEC_PATH):
    return json.load(open(path))


def run_check(ifc_path, spec=None, display_name=None):
    """Audit one IFC file. Returns the report dict used by both front ends."""
    spec = spec or load_spec()
    schema, ents = parse_spf(ifc_path)
    idx = build_index(ents)
    results, m_fail, score_num, score_den = [], [], 0, 0
    for r in spec["requirements"]:
        ok, det = evaluate(r, schema, ents, idx)
        results.append({
            "id": r["id"], "title": r["title"], "pass": ok, "detail": det,
            "mandatory": r["mandatory"], "weight": r.get("weight", 1),
            "category": r["category"], "rationale": r["rationale"],
            "sources": [f"{s['standard']} {s['clause']} ({s['node']})"
                        for s in r["sources"]],
        })
        if r["mandatory"]:
            if not ok:
                m_fail.append(r["id"])
        else:
            w = r.get("weight", 1)
            score_den += w
            score_num += w * ok
    score = score_num / score_den if score_den else 0.0
    if not m_fail and score >= 0.8:
        verdict, level = "CDT-READY for the PdM use case", "ready"
    elif (not m_fail and score >= 0.5) or (len(m_fail) == 1 and score >= 0.7):
        verdict, level = "CONDITIONAL - usable to pilot, close the gaps below", "conditional"
    else:
        verdict, level = "NOT READY for the PdM use case", "not_ready"
    return {"model": display_name or ifc_path, "schema": schema,
            "entities": len(ents), "results": results, "mandatory_failed": m_fail,
            "recommended_score": round(score, 3), "verdict": verdict, "level": level}


# ---------------------------------------------------------------- CLI
def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = run_check(sys.argv[1])
    print(f"model: {out['model']}")
    print(f"schema: {out['schema']}, entities: {out['entities']}")
    print("=" * 76)
    for r in out["results"]:
        lvl = "MANDATORY" if r["mandatory"] else f"w={r['weight']}"
        print(f"[{'PASS' if r['pass'] else 'FAIL'}] {r['id']} ({lvl}) {r['title']}")
        print(f"       {r['detail']}")
        print(f"       per {r['sources'][0]}"
              + (f" +{len(r['sources'])-1} more" if len(r["sources"]) > 1 else ""))
    print("=" * 76)
    print(f"mandatory failed: {out['mandatory_failed'] or 'none'}   "
          f"recommended score: {out['recommended_score']:.0%}")
    print(f"VERDICT: {out['verdict']}")
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        json.dump(out, open(jp, "w"), indent=2)
        print(f"written: {jp}")
    sys.exit(0 if out["level"] == "ready" else 2)


if __name__ == "__main__":
    main()
