#!/usr/bin/env python3
"""Local web UI for the ISO 19650 PdM knowledge graph and IFC readiness checker.

    python3 tmp/serve.py            # http://localhost:8000, opens the browser
    python3 tmp/serve.py 9000       # different port

Three tabs:
  Check IFC        - drag-drop an IFC model, get the CDT-readiness verdict
  Requirements     - the 13 checks with what each is for and what breaks without it
  Explore graph    - browse the knowledge graph, including the PdM use case itself,
                     without writing Cypher

Stdlib only - no pip install. The audit logic is imported from check_ifc_pdm so
the CLI and this UI can never disagree, and the graph is read from the same five
extraction JSONs that Neo4j was loaded from, so no driver and no server needed.

Upload transport is a raw POST body plus an X-Filename header, not multipart:
IFC files are a single binary blob, so multipart buys nothing and cgi.FieldStorage
is deprecated in 3.11 and gone in 3.13.
"""
import json, os, sys, tempfile, threading, webbrowser, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from check_ifc_pdm import run_check, load_spec          # noqa: E402

NEO4J_BROWSER = os.environ.get("NEO4J_BROWSER", "http://192.168.110.146:7474")
KG_FILES = ["iso19650-1_extraction_v4.json", "iso19650-2_extraction_v1.json",
            "iso19650-3_extraction_v1.2.json", "iso19650-4_extraction_v1.json",
            "iso19650-5_extraction_v1.json", "iso19650-6_extraction_v2.json"]
MAX_UPLOAD = 400 * 1024 * 1024
_cache = {}


def _load_kg():
    if "kg" not in _cache:
        out = []
        for f in KG_FILES:
            p = os.path.join(ROOT, f)
            if os.path.exists(p):
                out.append((f, json.load(open(p))))
        _cache["kg"] = out
    return _cache["kg"]


def kg_stats():
    parts, nodes, rels, high = [], 0, 0, 0
    for f, d in _load_kg():
        h = sum(1 for n in d["nodes"] if n.get("pdm_relevance") == "high")
        parts.append({"standard": d["standard"], "file": f, "nodes": len(d["nodes"]),
                      "rels": len(d["relationships"]), "high": h})
        nodes += len(d["nodes"]); rels += len(d["relationships"]); high += h
    return {"parts": parts, "nodes": nodes, "rels": rels, "high": high,
            "browser": NEO4J_BROWSER}


def graph_data():
    """Whole graph, flattened for the browser. ~250 KB - fine over localhost."""
    nodes, edges = [], []
    for _, d in _load_kg():
        # "ISO 19650-1:2018" -> "ISO 19650-1": the year is display noise here and
        # the colour/filter keys in the page are keyed on the part alone
        std = d["standard"].split(":")[0].strip()
        for n in d["nodes"]:
            nodes.append({"id": n["id"], "name": n["name"], "label": n["label"],
                          "part": std, "pdm": n.get("pdm_relevance", "low"),
                          "def": n["definition"], "std": n["provenance"]["standard"],
                          "cl": n["provenance"]["clause"], "note": n.get("note", "")})
        for r in d["relationships"]:
            edges.append({"s": r["from"], "t": r["to"], "type": r["type"],
                          "std": r["provenance"]["standard"],
                          "cl": r["provenance"]["clause"], "note": r.get("note", "")})
    return {"nodes": nodes, "edges": edges}


def method_stats():
    """Live numbers for the Method page: gates from the last harness run,
    part sizes and interpretive-edge counts computed from the files, and the
    dated draft-extractor benchmark (a recorded experiment, not recomputed)."""
    ks = kg_stats()
    out = {"parts": ks["parts"], "nodes": ks["nodes"], "rels": ks["rels"]}
    try:
        out["metrics"] = json.load(open(os.path.join(HERE, "evaluation_metrics.json")))
    except Exception:
        out["metrics"] = None
    uc = conf = 0
    for _, d in _load_kg():
        for r in d["relationships"]:
            if r["provenance"]["standard"] == "USE-CASE EXTENSION":
                uc += 1
            if r.get("note", "").startswith("CONFLICT"):
                conf += 1
    out["uc_edges"], out["conflicts"] = uc, conf
    out["benchmark"] = {
        "date": "2026-07-29",
        "note": "draft_extractor v2 scored against the four hand-curated gold files; "
                "the gold file's own standard is excluded from the reuse registry so "
                "the resolver cannot cheat.",
        "rows": [  # raw counts measured 2026-07-29; percentages are computed in the page
            {"part": "ISO 19650-1", "created": 33, "createdMatched": 32,
             "termFound": 33, "goldTerms": 34, "found": 33, "goldNames": 82},
            {"part": "ISO 19650-4", "created": 4, "createdMatched": 4,
             "termFound": 4, "goldTerms": 4, "found": 4, "goldNames": 22},
            {"part": "ISO 19650-5", "created": 14, "createdMatched": 14,
             "termFound": 14, "goldTerms": 14, "found": 17, "goldNames": 84},
            {"part": "ISO 19650-6", "created": 5, "createdMatched": 5,
             "termFound": 5, "goldTerms": 5, "found": 5, "goldNames": 86},
        ],
        "denominator_note": "goldNames counts unique node names after suffix "
            "normalization, which is why Part 6 shows 86 for a 90-node file.",
    }
    return out


PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISO 19650 PdM - readiness checker and graph explorer</title>
<style>
:root{--bg:#fbfbfa;--fg:#1a1a18;--mut:#6b6b66;--line:#e2e2dd;--card:#fff;
--ok:#1a7f4b;--okbg:#e8f5ee;--bad:#b3261e;--badbg:#fdeceb;--warn:#8a6100;--warnbg:#fdf3e0;--acc:#2f5fd0;
--p1:#2f6fd0;--p2:#0f8f7a;--p3:#c9761b;--p4:#4e7a27;--p5:#8353c9;--p6:#c4384f;--edge:#c8c8c2}
@media(prefers-color-scheme:dark){:root{--bg:#16161a;--fg:#e8e8e4;--mut:#9a9a94;--line:#2e2e34;--card:#1e1e23;
--ok:#5ec98d;--okbg:#12291d;--bad:#f08b84;--badbg:#2c1614;--warn:#e0b355;--warnbg:#2b2110;--acc:#7fa4f5;
--p1:#6f9ef0;--p2:#3fc0a8;--p3:#e0a256;--p4:#8fbf5f;--p5:#ad83ef;--p6:#ef7286;--edge:#3a3a42}}
:root[data-theme=light]{--bg:#fbfbfa;--fg:#1a1a18;--mut:#6b6b66;--line:#e2e2dd;--card:#fff;--edge:#c8c8c2;
--ok:#1a7f4b;--okbg:#e8f5ee;--bad:#b3261e;--badbg:#fdeceb;--warn:#8a6100;--warnbg:#fdf3e0;--acc:#2f5fd0;
--p1:#2f6fd0;--p2:#0f8f7a;--p3:#c9761b;--p4:#4e7a27;--p5:#8353c9;--p6:#c4384f}
:root[data-theme=dark]{--bg:#16161a;--fg:#e8e8e4;--mut:#9a9a94;--line:#2e2e34;--card:#1e1e23;--edge:#3a3a42;
--ok:#5ec98d;--okbg:#12291d;--bad:#f08b84;--badbg:#2c1614;--warn:#e0b355;--warnbg:#2b2110;--acc:#7fa4f5;
--p1:#6f9ef0;--p2:#3fc0a8;--p3:#e0a256;--p4:#8fbf5f;--p5:#ad83ef;--p6:#ef7286}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px 56px}
h1{font-size:20px;margin:0 0 4px;letter-spacing:-.01em}
h2{font-size:15px;margin:30px 0 12px}
.sub{color:var(--mut);font-size:13.5px;margin:0 0 18px}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin-bottom:20px}
.tabs button{background:none;border:none;border-bottom:2px solid transparent;padding:9px 15px;
font:inherit;font-size:14px;color:var(--mut);cursor:pointer;margin-bottom:-1px}
.tabs button.on{color:var(--fg);border-bottom-color:var(--acc);font-weight:600}
.tab{display:none}.tab.on{display:block}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:10px 14px;min-width:104px}
.stat b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.stat span{color:var(--mut);font-size:11.5px;text-transform:uppercase;letter-spacing:.05em}
#drop{border:2px dashed var(--line);border-radius:12px;background:var(--card);padding:34px 20px;
text-align:center;cursor:pointer;transition:.15s}
#drop:hover,#drop.over{border-color:var(--acc);background:color-mix(in srgb,var(--acc) 6%,var(--card))}
#drop p{margin:6px 0 0;color:var(--mut);font-size:13px}
#drop strong{font-size:15.5px}
.verdict{border-radius:11px;padding:16px 18px;margin:20px 0 14px;border:1px solid}
.verdict.ready{background:var(--okbg);border-color:var(--ok)}
.verdict.conditional{background:var(--warnbg);border-color:var(--warn)}
.verdict.not_ready{background:var(--badbg);border-color:var(--bad)}
.verdict h3{margin:0 0 4px;font-size:16.5px}.verdict .meta{font-size:13px;color:var(--mut)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:9px;background:var(--card)}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);font-weight:600}
tr:last-child td{border-bottom:none}
.tag{display:inline-block;padding:1px 7px;border-radius:5px;font-size:11px;font-weight:600;white-space:nowrap}
.tag.pass{background:var(--okbg);color:var(--ok)}.tag.fail{background:var(--badbg);color:var(--bad)}
.tag.m{background:color-mix(in srgb,var(--fg) 9%,transparent);color:var(--fg)}
.det{color:var(--mut);font-size:12.5px;margin-top:3px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.src{color:var(--mut);font-size:11.5px;margin-top:3px}
a{color:var(--acc)}
.bar{height:7px;border-radius:4px;background:var(--line);overflow:hidden;margin-top:8px;max-width:280px}
.bar i{display:block;height:100%}
.hint{color:var(--mut);font-size:12.5px;margin-top:8px}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;
background:color-mix(in srgb,var(--fg) 6%,transparent);padding:1px 5px;border-radius:4px}
button.b{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--card);color:var(--fg);
padding:5px 11px;border-radius:7px;cursor:pointer}
button.b:hover{border-color:var(--acc)}
button.b.on{background:var(--acc);border-color:var(--acc);color:#fff}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid var(--line);
border-top-color:var(--acc);border-radius:50%;animation:sp .7s linear infinite;vertical-align:-2px}
@keyframes sp{to{transform:rotate(360deg)}}
/* graph tab */
.gbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
.gbar input[type=search]{font:inherit;font-size:13px;padding:5px 10px;border-radius:7px;
border:1px solid var(--line);background:var(--card);color:var(--fg);min-width:190px}
.gbar label{font-size:12.5px;color:var(--mut);display:inline-flex;gap:4px;align-items:center;cursor:pointer}
.gwrap{display:grid;grid-template-columns:1fr 320px;gap:12px}
@media(max-width:900px){.gwrap{grid-template-columns:1fr}}
#cv{width:100%;height:600px;background:var(--card);border:1px solid var(--line);
border-radius:10px;display:block;cursor:grab;touch-action:none}
#cv.drag{cursor:grabbing}
#panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;
max-height:600px;overflow-y:auto;font-size:13px}
#panel h3{margin:0 0 6px;font-size:15px;line-height:1.3}
#panel .k{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.05em;margin:12px 0 3px}
#panel .nb{padding:4px 0;border-bottom:1px solid var(--line);cursor:pointer}
#panel .nb:hover{color:var(--acc)}
#panel .nb:last-child{border-bottom:none}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:-1px}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin-top:8px}
/* fullscreen graph */
.gwrap.fs{display:block;background:var(--bg);padding:0}
.gwrap.fs #cv{height:100vh;border:none;border-radius:0}
.gwrap.fs #panel{position:fixed;top:14px;right:14px;width:360px;max-height:calc(100vh - 28px);
box-shadow:0 8px 32px rgba(0,0,0,.35);display:none;z-index:10}
.gwrap.fs #panel.show{display:block}
#fsbar{display:none}
.gwrap.fs #fsbar{display:flex;gap:8px;position:fixed;top:14px;left:14px;z-index:10}
.pclose{display:none;float:right;font:inherit;font-size:15px;line-height:1;border:none;
background:none;color:var(--mut);cursor:pointer;padding:2px 6px}
.pclose:hover{color:var(--fg)}
.gwrap.fs .pclose{display:block}
/* method page */
.pipe{display:flex;flex-wrap:wrap;gap:0;align-items:stretch;margin:14px 0}
.stage{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;
flex:1 1 150px;min-width:150px;opacity:0;animation:rise .5s ease forwards}
.stage b{display:block;font-size:13.5px;margin-bottom:4px}
.stage span{font-size:12px;color:var(--mut)}
.stage .tag{margin-top:6px}
.arrow{flex:0 0 34px;display:flex;align-items:center;justify-content:center;position:relative;
color:var(--mut);font-size:17px}
.arrow i{position:absolute;width:6px;height:6px;border-radius:50%;background:var(--acc);
left:2px;animation:flowdot 1.6s linear infinite}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes flowdot{0%{left:2px;opacity:0}15%{opacity:1}85%{opacity:1}100%{left:26px;opacity:0}}
@media(prefers-reduced-motion:reduce){.stage{animation:none;opacity:1}.arrow i{animation:none;display:none}}
@media(max-width:760px){.pipe{flex-direction:column}.arrow{transform:rotate(90deg);flex-basis:26px}}
.meterrow{display:grid;grid-template-columns:190px 1fr 130px;gap:12px;align-items:center;
padding:8px 0;border-bottom:1px solid var(--line);font-size:13.5px}
.meterrow:last-child{border-bottom:none}
.meter{height:10px;border-radius:5px;background:color-mix(in srgb,var(--fg) 8%,transparent);overflow:hidden}
.meter i{display:block;height:100%;width:0;background:var(--ok);transition:width 1.1s cubic-bezier(.2,.7,.2,1)}
.meter i.acc{background:var(--acc)}.meter i.warn{background:var(--warn)}
.meterrow .val{font-variant-numeric:tabular-nums;text-align:right;color:var(--mut)}
@media(max-width:640px){.meterrow{grid-template-columns:1fr;gap:4px}.meterrow .val{text-align:left}}
.pol h2{margin-top:26px}
.pol p,.pol li{font-size:14px;color:var(--fg)}
.pol .src{font-size:12.5px}
/* requirements tab */
.callout{background:var(--card);border:1px solid var(--line);
border-radius:9px;padding:14px 16px;margin-bottom:14px}
.callout h3{margin:0 0 6px;font-size:14.5px}
.callout p{margin:0 0 8px;font-size:13.5px;color:var(--mut)}
.req{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:12px}
.reqhead{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:4px}
.reqhead b{font-size:14.5px}
.req .k{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.05em;margin:11px 0 2px}
.req>div:not(.k):not(.reqhead):not(.cite){font-size:13.5px}
.tag.w{background:color-mix(in srgb,var(--acc) 14%,transparent);color:var(--acc)}
.cite{background:color-mix(in srgb,var(--fg) 3.5%,transparent);border-radius:7px;
padding:9px 11px;margin:7px 0;font-size:13px}
.cite a{font-size:12px}
/* folder tree */
.tree summary{cursor:pointer;list-style:none;display:flex;gap:9px;align-items:baseline;
padding:6px 8px;border-radius:7px}
.tree summary::-webkit-details-marker{display:none}
.tree summary::before{content:'\25B8';font-size:10px;color:var(--mut);width:10px;flex:none;
display:inline-block;transition:transform .12s}
.tree details[open]>summary::before{transform:rotate(90deg)}
.tree summary:hover{background:color-mix(in srgb,var(--fg) 5%,transparent)}
.grp>summary{font-weight:600;font-size:14.5px;padding:10px 8px;margin-top:6px}
.grp>summary small{font-weight:400;color:var(--mut);font-size:12.5px}
.node{margin-left:19px}
.node>summary b{font-weight:600;font-size:13.5px}
.fields{margin-left:46px;padding:2px 0 12px}
.f{display:grid;grid-template-columns:158px 1fr;gap:12px;padding:5px 0;font-size:13.5px;
align-items:start}
.f>span:first-child{color:var(--mut);font-size:11px;text-transform:uppercase;
letter-spacing:.05em;padding-top:3px}
.mod{font-size:10.5px;padding:1px 6px;border-radius:4px;font-weight:600;white-space:nowrap}
.mod.normative{background:color-mix(in srgb,var(--ok) 18%,transparent);color:var(--ok)}
.mod.informative{background:color-mix(in srgb,var(--fg) 10%,transparent);color:var(--mut)}
.mod.mixed{background:color-mix(in srgb,var(--acc) 15%,transparent);color:var(--acc)}
.mod.interpretive{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}
.cat{font-size:11px;color:var(--mut);font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.rule{display:grid;grid-template-columns:118px 1fr;gap:10px;font-size:13px;padding:3px 0}
.rule>span:first-child{font-weight:600}
@media(max-width:640px){.f,.rule{grid-template-columns:1fr;gap:2px}.fields{margin-left:24px}}
</style></head><body><div class="wrap">
<h1>ISO 19650 &rarr; Predictive Maintenance</h1>
<p class="sub">Readiness checker for IFC models, and an explorer for the knowledge graph they are checked against.</p>
<div class="tabs">
  <button id="t1" class="on" onclick="tab(1)">Check IFC</button>
  <button id="t2" onclick="tab(2)">Requirements &amp; why</button>
  <button id="t3" onclick="tab(3)">Explore graph</button>
  <button id="t4" onclick="tab(4)">Method &amp; accuracy</button>
  <button id="t5" onclick="tab(5)">Policies &amp; privacy</button>
</div>

<section id="s1" class="tab on">
  <div class="stats" id="stats"></div>
  <div id="drop"><strong>Drop an IFC file here</strong>
    <p>or click to choose &mdash; .ifc / .ifcxml, stays on this machine</p>
    <input type="file" id="file" accept=".ifc,.ifcxml,.ifczip" hidden></div>
  <div id="out"></div>
  <h2>Requirements <span style="font-weight:400;color:var(--mut);font-size:13px">(generated from the graph)</span></h2>
  <div class="scroll"><table id="spec"><thead><tr><th>ID</th><th>Requirement</th><th>Level</th><th>Derived from</th></tr></thead><tbody></tbody></table></div>
  <p class="hint">Same audit from the terminal: <code>python3 tmp/check_ifc_pdm.py model.ifc --json report.json</code></p>
</section>

<section id="s2" class="tab">
  <div id="why"></div>
  <div id="reqs"></div>
</section>

<section id="s3" class="tab">
  <div class="gbar">
    <strong style="font-size:13px">View:</strong>
    <button class="b on" data-v="usecase" onclick="preset(this)">PdM use case</button>
    <button class="b" data-v="high" onclick="preset(this)">High-PdM only</button>
    <button class="b" data-v="all" onclick="preset(this)">Everything</button>
  </div>
  <div class="gbar">
    <input type="search" id="q" placeholder="Search name or id&hellip;" oninput="rebuild()">
    <span id="parts"></span>
    <label title="Clicking a node hides everything that is not connected to it">
      <input type="checkbox" id="focus"> focus on click</label>
    <button class="b" onclick="fit()">Fit</button>
    <button class="b" onclick="rebuild(1)">Re-layout</button>
    <button class="b" onclick="toggleFS()">&#x26F6; Fullscreen</button>
    <button class="b" id="back" style="display:none" onclick="unfocus()">&larr; Back</button>
    <span class="hint" id="gcount"></span>
  </div>
  <div class="gwrap" id="gwrap">
    <div id="fsbar">
      <button class="b" onclick="fit()">Fit</button>
      <button class="b" id="fsback" style="display:none" onclick="unfocus()">&larr; Back</button>
      <button class="b" onclick="toggleFS()">&#x2715; Exit (Esc)</button>
    </div>
    <canvas id="cv"></canvas>
    <div id="panel"><p class="hint">Click a node to read its definition, its clause, and its neighbours.
      Drag to move a node, scroll to zoom, drag the background to pan.</p></div>
  </div>
  <div class="legend" id="legend"></div>
</section>

<section id="s4" class="tab">
  <div class="row" style="margin-bottom:10px">
    <button class="b on" id="mlen" onclick="setMLang('en')">English</button>
    <button class="b" id="mlvi" onclick="setMLang('vi')">Tiếng Việt</button>
  </div>
  <p class="sub" id="msub"></p>
  <div class="stats" id="mcards"></div>
  <h2 id="mh_pipe"></h2>
  <div class="pipe" id="pipe"></div>
  <p class="hint" id="mhint_pipe"></p>
  <h2 id="mh_gates"></h2>
  <div id="gates" class="scroll" style="padding:6px 14px"></div>
  <h2 id="mh_bench"></h2>
  <p class="hint" id="mhint_bench" style="margin-top:0"></p>
  <div id="bench" class="scroll" style="padding:6px 14px"></div>
  <p class="hint" id="benchnote"></p>
</section>

<section id="s5" class="tab pol">
  <p class="sub" style="margin-top:4px">What this project does and does not do with data. Research
  software - plain statements, no legalese.</p>

  <h2>Your uploaded IFC models</h2>
  <ul>
   <li><b>Processing is entirely local.</b> An uploaded model is written to a temporary file, audited
     in-process, and the temporary file is <b>deleted immediately</b> after the check - success or
     failure. Nothing is transmitted to any external service.</li>
   <li><b>What is kept:</b> nothing. The report exists only in your browser; download it if you want a
     record. The server prints a single console line (file name, verdict, score) to its own terminal.</li>
   <li><b>No cookies, no analytics, no trackers, no external requests.</b> This page is fully
     self-contained; the only outbound link is the Neo4j Browser link you click yourself.</li>
  </ul>

  <h2>Copyright of the source standards</h2>
  <ul>
   <li>The ISO 19650 series is copyrighted by ISO/BSI. <b>The PDFs are never distributed</b> with this
     repository or Docker image; each team member supplies licensed copies.</li>
   <li>The extraction JSONs and the Cypher export contain limited verbatim definitions with clause-level
     provenance, produced for research purposes, and are <b>excluded from version control</b> - they are
     shared within the project team only.</li>
   <li>The audit report shown to you cites <i>clause numbers</i>, not the standards' text - verify
     wording against your own licensed copy.</li>
  </ul>

  <h2>Personal data inside health-and-safety records</h2>
  <ul>
   <li>The ISO 19650-6 schema fields <i>Affected party / Raised by / Owned by</i> can identify people.
     The standard itself notes "privacy can need protection" and prefers organizational, project or
     role-based identification over personal identification (Table A.1, footnote b). This project adopts
     that as policy for any instance data it ever holds.</li>
   <li>Generalization (ISO 19650-6, 3.3) - removing or replacing personal and protected characteristics -
     is the required step before any wider sharing of learning material.</li>
  </ul>

  <h2>Data governance defaults (proposed)</h2>
  <p class="src">The knowledge graph machine-detected two contradictory obligations between ISO 19650-5
  and ISO 19650-6 (full analysis: <code>tmp/conflict_findings.md</code>). For any deployment, this
  project proposes:</p>
  <ul>
   <li><b>Retention:</b> registers keep an append-only spine of anonymizable stubs forever; sensitive
     payloads within them are purgeable; every derived copy (exports, caches, model-training snapshots)
     is purgeable. Satisfies the ISO 19650-6 no-deletion rule and the ISO 19650-5 purging rule at once.</li>
   <li><b>Sharing:</b> inside the appointed project/asset team, health-and-safety information flows
     freely (ISO 19650-6, 4.5.2); to anyone outside the appointment chain, the ISO 19650-5 third-party
     provision assessment runs first and generalized records are the sharing currency.</li>
  </ul>

  <h2>Security posture of this software</h2>
  <ul>
   <li>The web UI binds to <code>127.0.0.1</code> by default (your machine only); Docker deployments bind
     the container network. There is no authentication layer - do not expose it to untrusted networks.</li>
   <li>Database credentials live in <code>.env</code> (git-ignored), never in code.</li>
   <li>The audit engine parses IFC as plain text with no code execution paths from file content.</li>
  </ul>
  <p class="src">Contact: the project team (Chulalongkorn University research project).</p>
</section>
</div><script>
const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let last=null;
function tab(n){for(const i of [1,2,3,4,5]){$('#t'+i).classList.toggle('on',i===n);$('#s'+i).classList.toggle('on',i===n)}
  if(n===2&&!REQ)loadReqs();
  if(n===3){if(!G)loadGraph();else{resize();draw()}}
  if(n===4&&!MET)loadMethod()}

/* ---------------- tab 1: IFC check ---------------- */
fetch('/api/kg').then(r=>r.json()).then(k=>{
  $('#stats').innerHTML=`
   <div class="stat"><b>${k.nodes}</b><span>KG nodes</span></div>
   <div class="stat"><b>${k.rels}</b><span>relationships</span></div>
   <div class="stat"><b>${k.high}</b><span>high&#8209;PdM</span></div>
   <div class="stat"><b>${k.parts.length}</b><span>standards</span></div>
   <div class="stat" style="min-width:auto"><b style="font-size:14px;padding-top:3px">
     <a href="${esc(k.browser)}" target="_blank" rel="noopener">Neo4j Browser &#8599;</a></b>
     <span>same data, Cypher</span></div>`;
});
const drop=$('#drop'),inp=$('#file');
drop.onclick=()=>inp.click();
inp.onchange=e=>{if(e.target.files[0])send(e.target.files[0])};
['dragenter','dragover'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.add('over')}));
['dragleave','drop'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.remove('over')}));
drop.addEventListener('drop',e=>{const f=e.dataTransfer.files[0];if(f)send(f)});
function send(f){
  $('#out').innerHTML=`<div class="verdict conditional"><h3><span class="spinner"></span>
    Checking ${esc(f.name)}</h3><div class="meta">${(f.size/1048576).toFixed(1)} MB</div></div>`;
  fetch('/api/check',{method:'POST',headers:{'X-Filename':encodeURIComponent(f.name)},body:f})
   .then(r=>r.json()).then(render)
   .catch(e=>$('#out').innerHTML=`<div class="verdict not_ready"><h3>Failed</h3>
     <div class="meta">${esc(e.message||e)}</div></div>`);
}
function render(d){
  if(d.error){$('#out').innerHTML=`<div class="verdict not_ready"><h3>Could not read the file</h3>
    <div class="meta">${esc(d.error)}</div></div>`;return}
  last=d;
  const pct=Math.round(d.recommended_score*100),gaps=d.results.filter(r=>!r.pass);
  const col=d.level==='not_ready'?'var(--bad)':d.level==='conditional'?'var(--warn)':'var(--ok)';
  $('#out').innerHTML=`
   <div class="verdict ${d.level}"><h3>${esc(d.verdict)}</h3>
     <div class="meta">${esc(d.model)} &middot; schema ${esc(d.schema)} &middot; ${d.entities} entities
       &middot; mandatory failed: ${d.mandatory_failed.length?d.mandatory_failed.join(', '):'none'}
       &middot; recommended score ${pct}%</div>
     <div class="bar"><i style="width:${pct}%;background:${col}"></i></div></div>
   ${gaps.length?`<p class="hint"><b>${gaps.length} gap${gaps.length>1?'s':''} to close:</b>
     ${gaps.map(g=>esc(g.id)).join(', ')} &mdash; see the
     <a href="#" onclick="tab(2);return false">Requirements</a> tab for what each one is for.</p>`:''}
   <div class="scroll"><table><thead><tr><th>ID</th><th>Check</th><th>Result</th></tr></thead><tbody>
   ${d.results.map(r=>`<tr>
     <td><code>${r.id}</code>${r.mandatory?'<br><span class="tag m">GATE</span>':''}</td>
     <td>${esc(r.title)}<div class="det">${esc(r.detail)}</div>
         <div class="src">per ${esc(r.sources[0])}${r.sources.length>1?' +'+(r.sources.length-1)+' more':''}</div></td>
     <td><span class="tag ${r.pass?'pass':'fail'}">${r.pass?'PASS':'FAIL'}</span></td></tr>`).join('')}
   </tbody></table></div>
   <div class="row" style="margin-top:14px"><button class="b" onclick="dl()">Download report JSON</button>
     <button class="b" onclick="window.print()">Print / PDF</button></div>`;
  if(REQ)drawReqs();          // fold the result into the requirements tree
  window.scrollTo({top:drop.offsetTop-20,behavior:'smooth'});
}
function dl(){if(!last)return;
  const b=new Blob([JSON.stringify(last,null,2)],{type:'application/json'}),u=URL.createObjectURL(b),
        a=document.createElement('a');
  a.href=u;a.download='pdm_readiness_'+last.model.replace(/[^\w.-]/g,'_')+'.json';a.click();
  URL.revokeObjectURL(u)}

/* ---------------- tab 2: requirements and why ---------------- */
let REQ=null;
function loadReqs(){fetch('/api/spec').then(r=>r.json()).then(s=>{REQ=s;drawReqs()})}
function drawReqs(){
  const R=REQ.requirements, gates=R.filter(r=>r.mandatory), scored=R.filter(r=>!r.mandatory);
  const tw=scored.reduce((a,r)=>a+(r.weight||1),0);
  $('#why').innerHTML=`
   <div class="callout"><h3>${esc(REQ.use_case)}</h3>
     <p style="margin-bottom:0">Acceptance criteria for an IFC model feeding this use case. In
     ISO 19650 terms this is EIR-level content. Derived from
     ${REQ.derived_from.map(f=>`<code>${esc(f)}</code>`).join(' ')}.</p></div>
   <div class="callout"><h3>How these ${R.length} requirements are produced</h3>
     <p>${esc(REQ.how_generated)}</p>
     <p style="margin-bottom:0"><b>They are not the use case.</b> The use case lives in the graph and
     describes the running loop (sensor &rarr; model &rarr; alert &rarr; work order &rarr; outcome).
     These requirements are its projection onto one deliverable: what an IFC file must contain for
     that loop to bind to it. Runtime artefacts such as the alert or the work order are deliberately
     absent &mdash; they are produced during operation, not found in a handover model.
     See the <a href="#" onclick="tab(3);return false">Explore graph</a> tab for the use case itself.</p></div>
   <div class="callout"><h3>How a verdict is decided</h3>
     ${Object.entries(REQ.verdict_rule).map(([k,v])=>
       `<div class="rule"><span>${esc(k.replace('_','-').toUpperCase())}</span><span>${esc(v)}</span></div>`).join('')}
     <p class="hint" style="margin:8px 0 0">${gates.length} gates, ${scored.length} scored
       requirements, total weight ${tw}.</p></div>
   <div class="callout"><h3>Normative or informative?</h3>
     <p style="margin-bottom:0">${esc(REQ.modality_note)}</p>
     <div style="margin-top:8px"><span class="mod normative">normative</span>
       <span class="mod informative">informative</span>
       <span class="mod mixed">mixed</span> &mdash; shown on every clause below.</div></div>
   <div class="row" style="margin:14px 0 6px">
     <button class="b" onclick="allDetails(true)">Expand all</button>
     <button class="b" onclick="allDetails(false)">Collapse all</button>
     <span class="hint" id="reqhint"></span></div>`;

  const res=last?Object.fromEntries(last.results.map(r=>[r.id,r.pass])):null;
  $('#reqhint').textContent=res?`showing the result of the last check: ${last.model}`:'';

  const node=r=>{
    const mods={};r.sources.forEach(x=>mods[x.modality]=(mods[x.modality]||0)+1);
    const badge=res==null?'':`<span class="tag ${res[r.id]?'pass':'fail'}">${res[r.id]?'PASS':'FAIL'}</span>`;
    return `<details class="node"><summary>
      <code>${r.id}</code> ${badge}
      <b>${esc(r.title)}</b>
      <span class="mod ${r.basis}">${r.basis}</span>
      <span class="cat">${esc(r.category)}</span>
      ${r.mandatory?'':`<span class="cat">w${r.weight||1}</span>`}</summary>
     <div class="fields">
       <div class="f"><span>Serves</span><span>${esc(r.loop_step)}</span></div>
       <div class="f"><span>Why it exists</span><span>${esc(r.rationale)}</span></div>
       <div class="f"><span>Without it</span><span>${esc(r.if_missing)}</span></div>
       <div class="f"><span>Checker looks for</span><span class="det">${esc(r.probe_human)}</span></div>
       ${res!=null?`<div class="f"><span>Last check</span><span class="det">${esc(
          last.results.find(x=>x.id===r.id).detail)}</span></div>`:''}
       <details class="node" style="margin-left:0"><summary>
         <span>Basis &mdash; ${r.sources.length} clause${r.sources.length>1?'s':''}
         (${Object.entries(mods).map(([k,v])=>v+' '+k).join(', ')})</span></summary>
         <div style="margin-left:19px">${r.sources.map(x=>`<div class="cite">
           <b>${esc(x.name)}</b> <span class="mod ${x.modality}">${x.modality}</span>
           <div class="src">${esc(x.standard)}, clause ${esc(x.clause)}
             &middot; <code>${esc(x.node)}</code> &middot; PdM ${esc(x.pdm_relevance)}</div>
           <div class="src" style="margin-top:4px">${esc(x.definition)}</div>
           <a href="#" onclick="gotoNode('${x.node}');return false">show in graph &rarr;</a>
           </div>`).join('')}</div></details>
     </div></details>`};

  $('#reqs').innerHTML=`<div class="tree">
    <details class="grp" open><summary>Mandatory gates
      <small>&mdash; ${gates.length} &middot; fail any one and the model cannot join the twin</small></summary>
      ${gates.map(node).join('')}</details>
    <details class="grp" open><summary>Scored requirements
      <small>&mdash; ${scored.length} &middot; total weight ${tw} &middot; each one unlocks more of the loop</small></summary>
      ${scored.map(node).join('')}</details></div>`;
}
function allDetails(open){document.querySelectorAll('#reqs details, #reqs .node')
  .forEach(d=>{if(d.tagName==='DETAILS')d.open=open})}
function gotoNode(id){tab(3);
  const go=()=>{const n=G.nodes.find(x=>x.id===id);if(!n)return;
    $('#q').value=n.name;document.querySelectorAll('[data-v]').forEach(x=>x.classList.remove('on'));
    rebuild(1);const m=N.find(x=>x.id===id);if(m)select(m)};
  if(G)go();else{loadGraph();setTimeout(go,700)}}

/* ---------------- tab 3: graph explorer ---------------- */
let G=null,N=[],E=[],byId={},sel=null,view='usecase',hidden=new Set(),focusId=null;
/* the PdM use case itself: the loop plus the inputs and outputs that make it a story */
const USECASE=['term_condition_monitoring_system','term_scada_system','term_condition_observation',
 'term_asset_operational_data','term_pdm_model','term_health_indicator','term_anomaly_event',
 'term_remaining_useful_life_prediction','term_maintenance_alert','term_maintenance_work_order',
 'term_maintenance_intervention_outcome','term_failure_mode','term_asset_failure_history',
 'term_maintenance_history','term_asset_criticality','term_asset_condition_duty',
 'term_hs_incident','term_near_miss','term_hs_risk','term_risk_treatment','term_treatment_control',
 'term_level_of_risk','term_likelihood','term_consequence','term_risk_urgency_prioritization',
 'term_hs_register','term_hs_properties','term_foreseen_trigger_event','trigger_maintenance_work',
 'term_security_information_requirements','term_asset','term_aim'];
const PCOL={'ISO 19650-1':'--p1','ISO 19650-2':'--p2','ISO 19650-3':'--p3',
            'ISO 19650-4':'--p4','ISO 19650-5':'--p5','ISO 19650-6':'--p6'};
const cssv=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
function loadGraph(){
  $('#gcount').textContent='loading...';
  fetch('/api/graph').then(r=>r.json()).then(g=>{
    G=g;g.nodes.forEach(n=>byId[n.id]=n);
    $('#parts').innerHTML=Object.keys(PCOL).map(p=>
      `<label><input type="checkbox" checked onchange="togglePart('${p}',this.checked)">
       <span class="dot" style="background:var(${PCOL[p]})"></span>${p.replace('ISO 19650-','P')}</label>`).join(' ');
    $('#legend').innerHTML=Object.keys(PCOL).map(p=>
      `<span><span class="dot" style="background:var(${PCOL[p]})"></span>${esc(p)}</span>`).join('')
      +'<span>node size = number of connections</span>';
    resize();rebuild(1);
  });
}
function togglePart(p,on){on?hidden.delete(p):hidden.add(p);rebuild(1)}
function preset(b){document.querySelectorAll('[data-v]').forEach(x=>x.classList.toggle('on',x===b));
  view=b.dataset.v;focusId=null;$('#back').style.display='none';$('#q').value='';rebuild(1)}
function focusOn(id){focusId=id;$('#back').style.display='';
  $('#fsback').style.display=isFS()?'':'none';rebuild(1);
  const m=N.find(x=>x.id===id);if(m)select(m)}
function unfocus(){focusId=null;$('#back').style.display='none';
  $('#fsback').style.display='none';rebuild(1)}
function rebuild(relayout){
  if(!G)return;
  const q=$('#q').value.trim().toLowerCase();
  let keep;
  if(focusId){keep=new Set([focusId]);
    G.edges.forEach(e=>{if(e.s===focusId)keep.add(e.t);if(e.t===focusId)keep.add(e.s)})}
  else if(view==='all')keep=new Set(G.nodes.map(n=>n.id));
  else if(view==='high')keep=new Set(G.nodes.filter(n=>n.pdm==='high').map(n=>n.id));
  else keep=new Set(USECASE.filter(s=>byId[s]));   // 'usecase', the default
  if(q&&!focusId){
    const hit=new Set(G.nodes.filter(n=>n.name.toLowerCase().includes(q)||n.id.includes(q)).map(n=>n.id));
    const grow=new Set(hit);
    G.edges.forEach(e=>{if(hit.has(e.s))grow.add(e.t);if(hit.has(e.t))grow.add(e.s)});
    keep=grow}
  const old={};N.forEach(n=>old[n.id]=n);
  N=G.nodes.filter(n=>keep.has(n.id)&&!hidden.has(n.part)).map(n=>{
    const p=!relayout&&old[n.id];
    return Object.assign({},n,{x:p?p.x:0,y:p?p.y:0,vx:0,vy:0,deg:0,pin:p?p.pin:false})});
  const ids=new Set(N.map(n=>n.id)),pos={};N.forEach(n=>pos[n.id]=n);
  E=G.edges.filter(e=>ids.has(e.s)&&ids.has(e.t)).map(e=>({...e,a:pos[e.s],b:pos[e.t]}));
  E.forEach(e=>{e.a.deg++;e.b.deg++});
  const done=()=>{
    $('#gcount').textContent=`${N.length} nodes, ${E.length} relationships`
      +(focusId?' (focused on '+byId[focusId].name+')':'');
    sel=focusId?N.find(n=>n.id===focusId)||null:null;
    fit()};
  if(relayout){seed();userMoved=false;
    sel=focusId?N.find(n=>n.id===focusId)||null:null;
    settle(N.length>200?760:440,done)}
  else done();
}
/* --------- deterministic layout, animated settle, then a dead stop ---------
   Seeded by phyllotaxis (no Math.random), so the same filter always converges to
   the same picture. The solve is rendered progressively - about 90 frames, ~1.5 s -
   so you watch it settle instead of it appearing fully formed, but alpha decays
   monotonically and is never re-triggered, so it comes to rest and stays there.
   Dragging runs one gentle tick per mouse move (simAlpha 0.10, versus the 0.25
   full restart the first version used) so neighbours follow a little; it stops the
   moment you stop moving. */
const SIM={CH:-1500,LD:95,LS:0.09,GR:0.035,VD:0.62,VMAX:28};
let simAlpha=0,simDecay=1,anim=null;
function seed(){
  const A=Math.PI*(3-Math.sqrt(5));
  N.forEach((n,i)=>{const r=16*Math.sqrt(0.5+i),a=i*A;
    n.x=r*Math.cos(a);n.y=r*Math.sin(a);n.vx=0;n.vy=0});
}
function tickOnce(){
  const n=N.length,{CH,LD,LS,GR,VD,VMAX}=SIM;if(!n)return;
  for(let i=0;i<n;i++){const a=N[i];
    for(let j=i+1;j<n;j++){const b=N[j];
      let dx=b.x-a.x,dy=b.y-a.y,d2=dx*dx+dy*dy;
      if(d2<36){dx=dx||(i%2?0.9:-0.9);dy=dy||0.9;d2=36}
      if(d2>360000)continue;
      const w=CH*simAlpha/d2;
      a.vx+=dx*w;a.vy+=dy*w;b.vx-=dx*w;b.vy-=dy*w}}
  for(const e of E){
    const dx=e.b.x-e.a.x,dy=e.b.y-e.a.y,d=Math.hypot(dx,dy)||1;
    const w=(d-LD)/d*simAlpha*LS;
    e.a.vx+=dx*w;e.a.vy+=dy*w;e.b.vx-=dx*w;e.b.vy-=dy*w}
  for(const a of N){
    a.vx-=a.x*GR*simAlpha;a.vy-=a.y*GR*simAlpha;
    a.vx*=VD;a.vy*=VD;
    const sp=Math.hypot(a.vx,a.vy);
    if(sp>VMAX){a.vx=a.vx/sp*VMAX;a.vy=a.vy/sp*VMAX}
    if(a.pin||a===drag)continue;
    a.x+=a.vx;a.y+=a.vy}
}
function settle(ticks,done){
  cancelAnimationFrame(anim);
  simAlpha=1;simDecay=Math.pow(0.0015,1/ticks);
  let left=ticks;
  const per=Math.max(1,Math.ceil(ticks/90));   // ~90 frames whatever the size
  const go=()=>{
    for(let k=0;k<per&&left>0;k++){tickOnce();simAlpha*=simDecay;left--}
    if(!userMoved)fit();else draw();
    if(left>0)anim=requestAnimationFrame(go);
    else{N.forEach(a=>{a.vx=a.vy=0});simAlpha=0;if(!userMoved)fit();else draw();
         if(done)done()}};
  anim=requestAnimationFrame(go);
}
const cv=$('#cv'),ctx=cv.getContext('2d');
let W=0,H=0,scale=1,tx=0,ty=0,drag=null,pan=null,hover=null,moved=false,userMoved=false;
function resize(){const r=cv.getBoundingClientRect(),dpr=devicePixelRatio||1;
  cv.width=Math.max(1,r.width*dpr);cv.height=Math.max(1,r.height*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);W=r.width;H=r.height}
addEventListener('resize',()=>{resize();draw()});
function fit(){
  if(!N.length){ctx.clearRect(0,0,W,H);return}
  const xs=N.map(n=>n.x),ys=N.map(n=>n.y);
  const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  scale=Math.min(W/(x1-x0+170),H/(y1-y0+120),2.0)||1;
  tx=W/2-(x0+x1)/2*scale;ty=H/2-(y0+y1)/2*scale;draw()}
function rad(n){return 4+Math.min(9,Math.sqrt(n.deg||1)*2.1)}
function draw(){
  ctx.clearRect(0,0,W,H);
  const nbr=sel?new Set(E.filter(e=>e.s===sel.id||e.t===sel.id).flatMap(e=>[e.s,e.t])):null;
  ctx.lineWidth=1;
  for(const e of E){
    const on=sel&&(e.s===sel.id||e.t===sel.id);
    ctx.strokeStyle=on?cssv('--acc'):cssv('--edge');
    ctx.globalAlpha=sel?(on?.95:.13):.5;
    ctx.beginPath();
    ctx.moveTo(e.a.x*scale+tx,e.a.y*scale+ty);
    ctx.lineTo(e.b.x*scale+tx,e.b.y*scale+ty);ctx.stroke()}
  ctx.globalAlpha=1;
  for(const a of N){
    const X=a.x*scale+tx,Y=a.y*scale+ty,r=rad(a)*Math.min(1.5,Math.max(.6,scale));
    const dim=sel&&!nbr.has(a.id);
    ctx.globalAlpha=dim?.2:1;
    ctx.beginPath();ctx.arc(X,Y,r,0,6.284);
    ctx.fillStyle=cssv(PCOL[a.part]||'--mut');ctx.fill();
    if(a===sel||a===hover){ctx.lineWidth=2.5;ctx.strokeStyle=cssv('--fg');ctx.stroke();ctx.lineWidth=1}
    if(a.pin){ctx.globalAlpha=dim?.2:.6;ctx.beginPath();ctx.arc(X,Y,r+3.5,0,6.284);
      ctx.strokeStyle=cssv('--mut');ctx.stroke()}
    if(!dim&&(scale>.7||a===sel||a===hover||N.length<50)){
      ctx.globalAlpha=.93;ctx.fillStyle=cssv('--fg');
      ctx.font='11px ui-sans-serif,-apple-system,sans-serif';ctx.textAlign='center';
      const t=a.name.length>30?a.name.slice(0,29)+'...':a.name;
      ctx.fillText(t,X,Y-r-4)}}
  ctx.globalAlpha=1}
function at(ev){const r=cv.getBoundingClientRect(),mx=ev.clientX-r.left,my=ev.clientY-r.top;
  let best=null,bd=1e9;
  for(const a of N){const dx=a.x*scale+tx-mx,dy=a.y*scale+ty-my,d=dx*dx+dy*dy;
    if(d<bd&&d<Math.pow(rad(a)*Math.min(1.5,Math.max(.6,scale))+8,2)){bd=d;best=a}}
  return {n:best,mx,my}}
cv.addEventListener('mousedown',ev=>{const{n,mx,my}=at(ev);moved=false;
  if(n){drag=n;select(n)}else{pan={mx,my,tx,ty};cv.classList.add('drag')}});
cv.addEventListener('mousemove',ev=>{
  const r=cv.getBoundingClientRect();
  if(drag){moved=true;drag.x=(ev.clientX-r.left-tx)/scale;drag.y=(ev.clientY-r.top-ty)/scale;
    drag.pin=true;simAlpha=0.10;tickOnce();simAlpha=0;draw();return}
  if(pan){moved=true;userMoved=true;tx=pan.tx+(ev.clientX-r.left-pan.mx);
    ty=pan.ty+(ev.clientY-r.top-pan.my);draw();return}
  const {n}=at(ev);if(n!==hover){hover=n;cv.style.cursor=n?'pointer':'grab';draw()}});
addEventListener('mouseup',()=>{
  if(drag&&!moved&&$('#focus').checked&&drag.id!==focusId)focusOn(drag.id);
  if(!drag&&!moved&&isFS())hidePanel();
  drag=null;pan=null;cv.classList.remove('drag')});
cv.addEventListener('dblclick',ev=>{const{n}=at(ev);
  if(n){if(n.pin){n.pin=false;draw()}else focusOn(n.id)}});
cv.addEventListener('wheel',ev=>{ev.preventDefault();
  const r=cv.getBoundingClientRect(),mx=ev.clientX-r.left,my=ev.clientY-r.top;
  const k=Math.exp(-ev.deltaY*0.0016),ns=Math.min(4,Math.max(.15,scale*k));
  tx=mx-(mx-tx)*(ns/scale);ty=my-(my-ty)*(ns/scale);scale=ns;userMoved=true;draw()},{passive:false});
function select(n){sel=n;
  const out=E.filter(e=>e.s===n.id),inc=E.filter(e=>e.t===n.id);
  const li=(e,dir)=>{const o=byId[dir==='out'?e.t:e.s];return `<div class="nb" onclick="jump('${o.id}')">
     <span class="dot" style="background:var(${PCOL[o.part]})"></span>
     ${dir==='out'?'&rarr;':'&larr;'} <b>${esc(e.type)}</b> ${esc(o.name)}
     <div class="src">${esc(e.std)} ${esc(e.cl)}</div></div>`};
  $('#panel').innerHTML=`
   <button class="pclose" onclick="hidePanel()" title="close">&#x2715;</button>
   <h3>${esc(n.name)}</h3>
   <div class="src"><span class="dot" style="background:var(${PCOL[n.part]})"></span>
     ${esc(n.part)} &middot; ${esc(n.label)} &middot; PdM ${esc(n.pdm)} &middot; <code>${esc(n.id)}</code></div>
   <div class="row" style="margin-top:10px">
     <button class="b" onclick="focusOn('${n.id}')">Show only this neighbourhood</button></div>
   <div class="k">Definition</div><div>${esc(n.def)}</div>
   <div class="k">Provenance</div><div>${esc(n.std)} &mdash; clause ${esc(n.cl)}</div>
   ${n.note?`<div class="k">Note</div><div class="src" style="font-size:12px">${esc(n.note)}</div>`:''}
   <div class="k">Outgoing (${out.length})</div>${out.map(e=>li(e,'out')).join('')||'<div class="src">none</div>'}
   <div class="k">Incoming (${inc.length})</div>${inc.map(e=>li(e,'in')).join('')||'<div class="src">none</div>'}`;
  if(isFS())$('#panel').classList.add('show');
  draw()}
function jump(id){const n=N.find(x=>x.id===id);
  if(n){select(n);tx=W/2-n.x*scale;ty=H/2-n.y*scale;draw()}
  else focusOn(id)}
/* ---- method & accuracy page ---- */
let MET=null;
function countUp(el,target,suffix){
  const t0=performance.now(),dur=900,from=0;
  const step=t=>{const k=Math.min(1,(t-t0)/dur);
    el.textContent=Math.round(from+(target-from)*(1-Math.pow(1-k,3))).toLocaleString()+(suffix||'');
    if(k<1)requestAnimationFrame(step)};
  requestAnimationFrame(step)}
function loadMethod(){fetch('/api/method').then(r=>r.json()).then(d=>{MET=d;drawMethod()})}
let MLANG='en';
function setMLang(l){MLANG=l;$('#mlen').classList.toggle('on',l==='en');
  $('#mlvi').classList.toggle('on',l==='vi');if(MET)drawMethod()}
const MT={
en:{sub:'How six copyrighted PDF standards became one verified knowledge graph, and exactly how accurate and complete the result is. Every number is produced by the evaluation harness (tmp/evaluate_kg.py) or computed live from the recorded raw counts - the formulas below show the arithmetic.',
 cards:['standards','KG nodes','relationships','clause references','interpretive edges','conflicts detected'],
 h_pipe:'The pipeline', h_gates:'Accuracy & coverage - the five acceptance gates (live from the last harness run)',
 h_bench:'How far the machine alone gets - measured ceiling',
 hint_pipe:'The machine stage is deterministic (same PDF in, same draft out). The curation stage is analyst judgment governed by a fixed protocol (tmp/extraction_protocol.md: 9 conventions). Nothing merges until all five gates pass.',
 hint_bench:'The draft generator scored against the hand-curated gold files. Green = fidelity of the terms layer it extracts. Blue = how much of the whole standard it reaches. The blue bar is a ceiling measurement, not a defect: the full pipeline (machine + curation + gates) produced the gold itself. Worked example, Part 1: 82 gold nodes = 34 Clause-3 terms (machine gets ~all) + 12 purposes from prose bullet lists + 10 principles + 4 CDE states from a figure + 4 perspectives from a table + ~18 body concepts that had to be recognized and sometimes NAMED. Part 6 sits lowest because its value is Tables 1-4, enumerations and annexes - invisible to sentence-level parsing. This measured gap is the quantitative case for the hybrid method.',
 stages:[['Licensed PDF','the source standard; never redistributed','input'],
  ['Text + page images','pdftotext for prose and tables, pdftoppm for figures - legends are read from images, never assumed','machine'],
  ['Machine first draft','terms verbatim with clause provenance, cross-reference edges, trigger phrases, figure-key chains - deterministic','machine'],
  ['Human curation','tables, annex lists, modality, cross-part reuse, PdM bridges - governed by the 9-rule protocol','judgment'],
  ['Five gates','structure, fidelity, references, traversability, coverage - machine-enforced; merge blocked on failure','machine'],
  ['Union knowledge graph','NODES nodes / RELS relationships across PARTS standards','output'],
  ['Products','Neo4j graph - 13 IFC requirements - readiness audits','output']],
 tags:{machine:'machine',judgment:'judgment',input:'input',output:'output'},
 gates:[['E1 structure','duplicate ids/names, dangling endpoints, closed vocabularies, pure ASCII'],
  ['E2 definition fidelity','every Clause-3 definition matched verbatim against its source PDF'],
  ['E3 reference validity','every provenance clause resolved against PDF heading inventories'],
  ['E4 traversability','0 orphans - one component - 16-step PdM spine - high-PdM reachable'],
  ['E5 term coverage','all source Clause-3 terms represented in the union']],
 fdel:'fidelity', fval:'validity', fcov:'coverage', fviol:'violations', fpass:'PASS',
 termfid:'term fidelity', reach:'whole-standard reach (machine alone)',
 fprec:'precision = correct / created', frec:'recall = found / gold terms',
 freach:'reach = found nodes / gold nodes',
 goldn:'% of gold nodes'},
vi:{sub:'Sáu bản PDF chuẩn có bản quyền trở thành một đồ thị tri thức đã kiểm chứng như thế nào, và kết quả chính xác - đầy đủ đến đâu. Mọi con số do harness đánh giá (tmp/evaluate_kg.py) sinh ra hoặc được tính trực tiếp từ số đếm thô đã ghi nhận - công thức bên dưới hiện rõ phép tính.',
 cards:['chuẩn ISO','node tri thức','quan hệ','tham chiếu điều khoản','cạnh suy diễn','mâu thuẫn phát hiện'],
 h_pipe:'Quy trình', h_gates:'Độ chính xác & độ phủ - 5 cổng nghiệm thu (số liệu sống từ lần chạy harness gần nhất)',
 h_bench:'Máy đơn độc đi được bao xa - trần đo được',
 hint_pipe:'Khâu máy là tất định (cùng PDF vào, cùng bản nháp ra). Khâu curation là phán đoán của người phân tích, bị ràng buộc bởi protocol cố định (tmp/extraction_protocol.md: 9 quy ước). Không gì được merge khi chưa qua đủ 5 cổng.',
 hint_bench:'Máy sinh bản nháp được chấm điểm so với các file gold do người curate. Xanh lá = độ trung thực của tầng term mà máy trích được. Xanh dương = máy với tới bao nhiêu phần của cả chuẩn. Thanh xanh dương là PHÉP ĐO TRẦN, không phải khuyết tật: chính pipeline đầy đủ (máy + curation + cổng) đã tạo ra bản gold. Ví dụ Part 1: 82 node gold = 34 term Clause 3 (máy bắt gần hết) + 12 purpose nằm trong danh sách gạch đầu dòng giữa văn xuôi + 10 principle + 4 trạng thái CDE từ hình vẽ + 4 perspective từ bảng + ~18 khái niệm thân bài phải nhận diện và đôi khi phải ĐẶT TÊN. Part 6 thấp nhất vì giá trị của nó nằm ở Tables 1-4, các enum và annex - vô hình với parse từng câu. Khoảng hở đo được này chính là luận cứ định lượng cho phương pháp hybrid.',
 stages:[['PDF có giấy phép','chuẩn nguồn; không bao giờ phân phối lại','input'],
  ['Văn bản + ảnh trang','pdftotext cho chữ và bảng, pdftoppm cho hình - chú giải hình đọc từ ảnh, không phỏng đoán','machine'],
  ['Bản nháp do máy','term nguyên văn kèm provenance điều khoản, cạnh cross-reference, trigger phrase, chuỗi key hình - tất định','machine'],
  ['Curation bởi người','bảng, danh sách annex, modality, tái sử dụng liên chuẩn, cầu nối PdM - theo protocol 9 quy ước','judgment'],
  ['5 cổng nghiệm thu','cấu trúc, trung thực, tham chiếu, truy vết được, độ phủ - máy cưỡng chế; không qua là không merge','machine'],
  ['Đồ thị tri thức hợp nhất','NODES node / RELS quan hệ trên PARTS chuẩn','output'],
  ['Sản phẩm','đồ thị Neo4j - 13 yêu cầu IFC - chấm mô hình','output']],
 tags:{machine:'máy',judgment:'phán đoán',input:'đầu vào',output:'đầu ra'},
 gates:[['E1 cấu trúc','trùng id/tên, cạnh treo, tập từ vựng đóng, ASCII thuần'],
  ['E2 trung thực định nghĩa','mọi định nghĩa Clause 3 so khớp nguyên văn với PDF nguồn'],
  ['E3 hợp lệ tham chiếu','mọi trích dẫn điều khoản resolve được trong đúng chuẩn của nó'],
  ['E4 truy vết đồ thị','0 node mồ côi - 1 thành phần liên thông - spine PdM 16 bước - high-PdM tới được'],
  ['E5 độ phủ thuật ngữ','toàn bộ term Clause 3 của nguồn có mặt trong đồ thị hợp nhất']],
 fdel:'độ trung thực', fval:'độ hợp lệ', fcov:'độ phủ', fviol:'vi phạm', fpass:'ĐẠT',
 termfid:'độ trung thực term', reach:'độ phủ toàn chuẩn (máy đơn độc)',
 fprec:'precision = số đúng / số máy tạo', frec:'recall = số tìm thấy / tổng term gold',
 freach:'độ phủ = node tìm thấy / node gold',
 goldn:'% node gold'}};
function drawMethod(){
  const T=MT[MLANG], m=MET.metrics||{};
  $('#msub').textContent=T.sub;
  $('#mh_pipe').textContent=T.h_pipe; $('#mh_gates').textContent=T.h_gates;
  $('#mh_bench').textContent=T.h_bench;
  $('#mhint_pipe').textContent=T.hint_pipe; $('#mhint_bench').textContent=T.hint_bench;
  const vals=[MET.parts.length,MET.nodes,MET.rels,m.E3_provenances_checked||0,MET.uc_edges,MET.conflicts];
  $('#mcards').innerHTML=vals.map((v,i)=>
    `<div class="stat"><b data-n="${v}">0</b><span>${T.cards[i]}</span></div>`).join('');
  document.querySelectorAll('#mcards b').forEach(b=>countUp(b,+b.dataset.n));
  $('#pipe').innerHTML=T.stages.map((x,i)=>{
    const d=x[1].replace('NODES',MET.nodes).replace('RELS',MET.rels).replace('PARTS',MET.parts.length);
    return `${i?'<div class="arrow">&#8594;<i style="animation-delay:'+(i*.2)+'s"></i></div>':''}
     <div class="stage" style="animation-delay:${i*.15}s"><b>${esc(x[0])}</b><span>${esc(d)}</span>
     <span class="tag ${x[2]==='judgment'?'w':'m'}" style="margin-top:6px;display:inline-block">${T.tags[x[2]]}</span></div>`}).join('');
  const e2t=m.E2_terms_total||0,e2v=m.E2_terms_verbatim||0,e2n=m.E2_terms_near||0,e2f=m.E2_terms_failed||0;
  const e3c=m.E3_provenances_checked||0,e3u=m.E3_unresolved||0;
  const cov=(m.E5_term_coverage||'0/0').split('/');
  const G=[
   [T.gates[0][0],T.gates[0][1],m.E1_structural_pass?100:0,
    `${T.fviol} = 0 → ${m.E1_structural_pass?T.fpass:'FAIL'}`,m.E1_structural_pass?T.fpass:'FAIL'],
   [T.gates[1][0],T.gates[1][1],e2t?Math.round(100*(e2t-e2f)/e2t):0,
    `${T.fdel} = (${e2v} + ${e2n}) / ${e2t} = ${e2t?Math.round(100*(e2v+e2n)/e2t):0}%`,
    `${e2v} + ${e2n} / ${e2t}`],
   [T.gates[2][0],T.gates[2][1],e3c?Math.round(100*(e3c-e3u)/e3c):0,
    `${T.fval} = ${(e3c-e3u).toLocaleString()} / ${e3c.toLocaleString()} = ${e3c?Math.round(100*(e3c-e3u)/e3c):0}%`,
    `${(e3c-e3u).toLocaleString()} / ${e3c.toLocaleString()}`],
   [T.gates[3][0],T.gates[3][1],m.E4_traversability_pass?100:0,
    `spine ${m.E4_spine||'?'} · high-PdM ${m.E4_high_pdm_reachable||'?'}`,
    m.E4_traversability_pass?T.fpass:'FAIL'],
   [T.gates[4][0],T.gates[4][1],100,
    `${T.fcov} = ${cov[0]} / ${cov[1]} = ${Math.round(100*cov[0]/cov[1])}%`,m.E5_term_coverage||'']];
  $('#gates').innerHTML=G.map(x=>`<div class="meterrow"><span><b>${esc(x[0])}</b><br>
    <span class="src">${esc(x[1])}</span><br><span class="src det">${esc(x[3])}</span></span>
    <div class="meter"><i data-w="${x[2]}"></i></div><span class="val">${esc(String(x[4]))}</span></div>`).join('');
  $('#bench').innerHTML=MET.benchmark.rows.map(r=>{
    const tp=Math.round(100*r.createdMatched/r.created),
          tr=Math.round(100*r.termFound/r.goldTerms),
          rc=Math.round(100*r.found/r.goldNames);
    return `
    <div class="meterrow"><span><b>${r.part}</b><br><span class="src">${T.termfid}</span><br>
      <span class="src det">${T.fprec} = ${r.createdMatched} / ${r.created} = ${tp}%<br>
      ${T.frec} = ${r.termFound} / ${r.goldTerms} = ${tr}%</span></span>
      <div class="meter"><i data-w="${tr}"></i></div><span class="val">${tp}% · ${tr}%</span></div>
    <div class="meterrow"><span><span class="src">${T.reach}</span><br>
      <span class="src det">${T.freach} = ${r.found} / ${r.goldNames} = ${rc}%</span></span>
      <div class="meter"><i class="acc" data-w="${rc}"></i></div><span class="val">${rc}% (${r.found}/${r.goldNames})</span></div>`}).join('');
  $('#benchnote').textContent=(MLANG==='vi'
    ?`Benchmark ngày ${MET.benchmark.date}: máy sinh bản nháp v2 chấm so với 4 file gold; chuẩn của chính file gold bị loại khỏi registry để bộ resolve không thể tự gian lận. ${MET.benchmark.denominator_note?'Ghi chú mẫu số: goldNames đếm tên node duy nhất sau khi chuẩn hoá hậu tố, nên Part 6 hiện 86 cho file 90 node.':''}`
    :`Benchmark of ${MET.benchmark.date}: ${MET.benchmark.note} ${MET.benchmark.denominator_note||''}`);
  setTimeout(()=>document.querySelectorAll('.meter i').forEach(i=>i.style.width=i.dataset.w+'%'),120);
}
/* ---- fullscreen mode ---- */
const gwrap=$('#gwrap');
function isFS(){return document.fullscreenElement===gwrap||document.webkitFullscreenElement===gwrap}
function toggleFS(){
  if(isFS()){(document.exitFullscreen||document.webkitExitFullscreen).call(document)}
  else{(gwrap.requestFullscreen||gwrap.webkitRequestFullscreen).call(gwrap)}}
function onFS(){
  gwrap.classList.toggle('fs',isFS());
  if(!isFS())$('#panel').classList.remove('show');
  $('#fsback').style.display=focusId?'':'none';
  setTimeout(()=>{resize();fit()},80)}
document.addEventListener('fullscreenchange',onFS);
document.addEventListener('webkitfullscreenchange',onFS);
function hidePanel(){$('#panel').classList.remove('show');sel=null;draw()}
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif p == "/api/kg":
            self._send(200, json.dumps(kg_stats()))
        elif p == "/api/spec":
            self._send(200, json.dumps(load_spec()))
        elif p == "/api/graph":
            self._send(200, json.dumps(graph_data()))
        elif p == "/api/method":
            self._send(200, json.dumps(method_stats()))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/check":
            return self._send(404, json.dumps({"error": "not found"}))
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return self._send(400, json.dumps({"error": "empty upload"}))
        if n > MAX_UPLOAD:
            return self._send(413, json.dumps(
                {"error": f"file over {MAX_UPLOAD // 1048576} MB; use the CLI for models this size"}))
        name = urllib.parse.unquote(self.headers.get("X-Filename", "model.ifc"))
        data, got = bytearray(), 0
        while got < n:                       # read in chunks, never assume one read
            chunk = self.rfile.read(min(1 << 20, n - got))
            if not chunk:
                break
            data += chunk; got += len(chunk)
        fd, tmp = tempfile.mkstemp(suffix=".ifc")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            report = run_check(tmp, display_name=os.path.basename(name))
            self._send(200, json.dumps(report))
            print(f"  checked {name}: {report['verdict']} "
                  f"(score {report['recommended_score']:.0%})", flush=True)
        except Exception as e:               # a malformed IFC must not kill the server
            self._send(200, json.dumps({"error": f"{type(e).__name__}: {e}"}))
            print(f"  FAILED {name}: {type(e).__name__}: {e}", flush=True)
        finally:
            os.unlink(tmp)

    def log_message(self, *a):
        pass                                 # quiet: we print our own one-liners


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    host = os.environ.get("HOST", "127.0.0.1")   # docker sets HOST=0.0.0.0
    load_spec()                              # fail fast if the spec is missing
    g = graph_data()                         # fail fast if an extraction file is missing
    url = f"http://localhost:{port}"
    print(f"PdM readiness UI  ->  {url}  (bound to {host})")
    print(f"graph             ->  {len(g['nodes'])} nodes / {len(g['edges'])} relationships")
    print(f"Neo4j Browser     ->  {NEO4J_BROWSER}\nCtrl-C to stop\n", flush=True)
    if host == "127.0.0.1":                  # only auto-open when running locally
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        ThreadingHTTPServer((host, port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
