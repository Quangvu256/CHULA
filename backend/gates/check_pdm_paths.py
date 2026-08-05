#!/usr/bin/env python3
"""Acid test for the merged ISO 19650 graph: is it actually traversable for the
predictive-maintenance use case, or just a pile of well-formed nodes?

Checks, in order:
  1. orphan nodes (no edge at all) and connected components
  2. the PdM spine - can a sensor reading reach a risk treatment / work order
  3. every high-PdM node is reachable from the spine
"""
import json, collections, os, sys
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

FILES = ["data/iso19650-1_extraction_v4.json", "data/iso19650-2_extraction_v1.json",
         "data/iso19650-3_extraction_v1.2.json", "data/iso19650-4_extraction_v1.json", "data/iso19650-5_extraction_v1.json",
         "data/iso19650-6_extraction_v2.json"]

nodes, edges = {}, []
for f in FILES:
    d = json.load(open(f))
    for n in d["nodes"]:
        nodes[n["id"]] = dict(n, _file=f)
    edges += [(r["from"], r["type"], r["to"]) for r in d["relationships"]]

adj = collections.defaultdict(list)     # directed
und = collections.defaultdict(set)      # undirected
for a, t, b in edges:
    adj[a].append((t, b))
    und[a].add(b)
    und[b].add(a)


def nm(i):
    return nodes[i]["name"] if i in nodes else f"<{i}>"


def path(src, dst, maxlen=8):
    """Shortest DIRECTED path src -> dst."""
    q, seen = collections.deque([(src, [src])]), {src}
    while q:
        cur, p = q.popleft()
        if cur == dst:
            return p
        if len(p) > maxlen:
            continue
        for t, nxt in adj[cur]:
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, p + [nxt]))
    return None


def show(p):
    if not p:
        return "   NO DIRECTED PATH"
    out = []
    for a, b in zip(p, p[1:]):
        t = next(t for t, x in adj[a] if x == b)
        out.append(f"   {nm(a)}\n     -[{t}]->")
    out.append(f"   {nm(p[-1])}")
    return "\n".join(out)


print("=" * 78)
print("1. STRUCTURE")
print("=" * 78)
orphans = [i for i in nodes if not und[i]]
print(f"nodes: {len(nodes)}  edges: {len(edges)}  orphans: {len(orphans)}")
for o in orphans:
    print(f"   ORPHAN {o} ({nodes[o]['_file']}) - {nm(o)}")

seen, comps = set(), []
for start in nodes:
    if start in seen:
        continue
    comp, q = set(), collections.deque([start])
    seen.add(start)
    while q:
        c = q.popleft()
        comp.add(c)
        for x in und[c]:
            if x not in seen:
                seen.add(x)
                q.append(x)
    comps.append(comp)
comps.sort(key=len, reverse=True)
print(f"connected components: {len(comps)} -> sizes {[len(c) for c in comps]}")
for c in comps[1:]:
    print(f"   ISLAND: {sorted(nm(i) for i in c)}")

print()
print("=" * 78)
print("2. THE PdM SPINE  (sensor -> decision -> action -> feedback)")
print("=" * 78)
SPINE = [
    ("term_condition_monitoring_system", "term_condition_observation", "sensor produces a reading"),
    ("term_condition_observation", "term_remaining_useful_life_prediction", "reading feeds the model"),
    ("term_remaining_useful_life_prediction", "term_maintenance_alert", "model raises an alert"),
    ("term_maintenance_alert", "term_maintenance_work_order", "alert becomes a work order"),
    ("term_maintenance_work_order", "term_maintenance_intervention_outcome", "work order is executed"),
    ("term_maintenance_intervention_outcome", "term_pdm_model", "outcome retrains the model"),
    # the Part 6 contribution: safety closes the loop
    ("term_remaining_useful_life_prediction", "term_level_of_risk", "prediction becomes a risk grade"),
    ("term_risk_urgency_prioritization", "term_maintenance_alert", "risk grade sets alert priority"),
    ("term_failure_mode", "term_hs_incident", "failure mode produces a safety incident"),
    ("term_hs_incident", "term_pdm_model", "incident record feeds the model"),
    ("term_maintenance_work_order", "term_risk_treatment", "work order registers as a risk treatment"),
    # the Part 5 contribution: security governs the loop
    ("term_security_information_requirements", "term_pdm_model", "security governs the model"),
    ("term_security_information_requirements", "term_hs_register", "security governs the H&S register"),
    # the Part 4 contribution: the exchange layer carries the data
    ("term_exchange_review_exception", "term_condition_observation",
     "6.4 exemption lets telemetry stream into the CDE"),
    ("decision_a_approve_sharing", "state_shared", "decision A moves information to shared"),
    ("decision_b_authorize_accept_publication", "state_published",
     "decision B publishes the information the twin consumes"),
]
ok = 0
for a, b, label in SPINE:
    p = path(a, b)
    mark = "PASS" if p else "FAIL"
    ok += bool(p)
    hops = f"{len(p) - 1} hop(s)" if p else "-"
    print(f"\n[{mark}] {label}  ({hops})")
    print(show(p))
print(f"\nspine: {ok}/{len(SPINE)} traversable")

print()
print("=" * 78)
print("3. HIGH-PdM REACHABILITY  (undirected, from the spine)")
print("=" * 78)
spine_ids = {x for a, b, _ in SPINE for x in (a, b)}
reach, q = set(spine_ids), collections.deque(spine_ids)
while q:
    c = q.popleft()
    for x in und[c]:
        if x not in reach:
            reach.add(x)
            q.append(x)
high = [i for i, n in nodes.items() if n.get("pdm_relevance") == "high"]
missing = [i for i in high if i not in reach]
print(f"high-PdM nodes: {len(high)}   reachable from the spine: {len(high) - len(missing)}")
for i in missing:
    print(f"   UNREACHABLE {i} - {nm(i)}")

per_file = collections.Counter(nodes[i]["_file"] for i in high)
for f in FILES:
    tot = sum(1 for n in nodes.values() if n["_file"] == f)
    print(f"   {f:34s} {per_file[f]:3d}/{tot:3d} high-PdM")

sys.exit(0 if ok == len(SPINE) and not orphans and len(comps) == 1 else 1)
