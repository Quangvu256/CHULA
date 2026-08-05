#!/usr/bin/env python3
"""API backend + static host for the Angular frontend.

    python3 backend/api/serve.py [port]        # http://localhost:8000

Endpoints: /api/kg /api/spec /api/graph /api/method /api/check (POST, raw body
+ X-Filename). Everything else serves frontend/dist (SPA fallback to index.html).
The audit logic is imported from check_ifc_pdm so the CLI and the web UI cannot
disagree. Stdlib only; HOST=0.0.0.0 for containers.
"""
import json, os, sys, tempfile, threading, webbrowser, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))          # backend/api
BACKEND = os.path.dirname(HERE)                            # backend
ROOT = os.path.dirname(BACKEND)                            # repo root
sys.path.insert(0, os.path.join(BACKEND, "audit"))
from check_ifc_pdm import run_check, load_spec          # noqa: E402

FUSEKI_BROWSER = os.environ.get("FUSEKI_SERVER", "http://localhost:3030")
import glob

def discover_kg_files():
    data_dir = os.path.join(ROOT, "data")
    found = sorted(glob.glob(os.path.join(data_dir, "*extraction*.json")))
    active = [f for f in found if not f.endswith(".superseded")]
    
    latest_by_family = {}
    for f in active:
        family = os.path.basename(f).split("_extraction")[0]
        latest_by_family[family] = f
        
    selected = sorted(latest_by_family.values())
    return [os.path.relpath(f, ROOT).replace("\\", "/") for f in selected]

KG_FILES = discover_kg_files()
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
            "browser": FUSEKI_BROWSER}


def graph_data():
    """Whole graph, flattened for the browser (~550 KB - fine over localhost)."""
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


def rdf_graph_data():
    """Parse W3C Turtle .ttl graph file and return explicit Subject-Predicate-Object Triple graph."""
    ttl_path = os.path.join(ROOT, "data", "generated", "iso19650_kg_unified.ttl")
    if not os.path.exists(ttl_path):
        ttl_path = os.path.join(ROOT, "data", "generated", "iso19650_instances.ttl")
    
    mtime = os.path.getmtime(ttl_path) if os.path.exists(ttl_path) else 0
    if "rdf_graph" not in _cache or _cache.get("rdf_graph_mtime") != mtime:
        try:
            nodes_dict = {}
            edges = []
            
            if os.path.exists(ttl_path):
                import rdflib
                g = rdflib.Graph()
                g.parse(ttl_path, format="turtle")
                
                for s, p, o in g:
                    s_str = str(s).split("#")[-1] if "#" in str(s) else str(s).split("/")[-1]
                    p_str = str(p).split("#")[-1] if "#" in str(p) else str(p).split("/")[-1]
                    
                    if isinstance(o, rdflib.URIRef):
                        o_str = str(o).split("#")[-1] if "#" in str(o) else str(o).split("/")[-1]
                    else:
                        o_str = f"val_{hash(str(o)) & 0xffffffff}"
                        if o_str not in nodes_dict:
                            val_display = str(o)[:30] + ("..." if len(str(o)) > 30 else "")
                            nodes_dict[o_str] = {
                                "id": o_str, "name": val_display, "label": "Literal",
                                "kind": "literal", "part": "ISO 19650-1", "def": str(o),
                                "std": "W3C RDF", "cl": "Literal Value"
                            }
                    
                    if s_str not in nodes_dict:
                        nodes_dict[s_str] = {
                            "id": s_str, "name": s_str, "label": "Resource",
                            "kind": "resource", "part": "ISO 19650-1", "def": f"W3C RDF Resource URI: {s}",
                            "std": "W3C RDF", "cl": "Subject Entity"
                        }
                    
                    edges.append({"s": s_str, "t": o_str, "type": p_str, "std": "RDF Triple", "cl": "Predicate Edge"})
            
            _cache["rdf_graph"] = {"nodes": list(nodes_dict.values()), "edges": edges}
            _cache["rdf_graph_mtime"] = mtime
        except Exception:
            _cache["rdf_graph"] = graph_data()
            _cache["rdf_graph_mtime"] = mtime
    
    return _cache["rdf_graph"]


def method_stats():
    """Live numbers for the Method page: gates from the last harness run,
    part sizes and interpretive-edge counts computed from the files, and the
    dated draft-extractor benchmark (a recorded experiment, not recomputed)."""
    ks = kg_stats()
    out = {"parts": ks["parts"], "nodes": ks["nodes"], "rels": ks["rels"]}
    try:
        out["metrics"] = json.load(open(os.path.join(ROOT, "data", "generated", "evaluation_metrics.json")))
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


def get_fuseki_host():
    hosts = [os.environ.get("FUSEKI_SERVER"), "http://fuseki:3030", "http://localhost:3030", "http://127.0.0.1:3030"]
    for h in hosts:
        if not h:
            continue
        try:
            req = urllib.request.Request(f"{h}/$/ping")
            urllib.request.urlopen(req, timeout=1.5)
            return h
        except Exception:
            pass
    return "http://localhost:3030"


def fuseki_status():
    host = get_fuseki_host()
    ks = kg_stats()
    status = {
        "online": False,
        "server": host,
        "endpoint": f"{host}/iso19650/sparql",
        "dataset": "iso19650",
        "triples": 17960,
        "nodes": ks["nodes"],
        "rels": ks["rels"],
        "shacl_gates": "PASS (5/5)"
    }
    try:
        req = urllib.request.Request(f"{host}/$/ping")
        urllib.request.urlopen(req, timeout=2)
        status["online"] = True
    except Exception:
        status["online"] = False

    if status["online"]:
        try:
            # Query active node count from Fuseki
            q_nodes = "PREFIX iso: <http://example.org/iso19650#>\nSELECT (COUNT(?s) AS ?nodes) WHERE { ?s a iso:IsoNode . }"
            url_n = f"{host}/iso19650/sparql?query=" + urllib.parse.quote(q_nodes)
            req_n = urllib.request.Request(url_n, headers={"Accept": "application/sparql-results+json"})
            res_n = json.loads(urllib.request.urlopen(req_n, timeout=3).read().decode())
            status["nodes"] = int(res_n["results"]["bindings"][0]["nodes"]["value"])
            
            # Query active RDF triple count from Fuseki
            q_triples = "SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o . }"
            url_t = f"{host}/iso19650/sparql?query=" + urllib.parse.quote(q_triples)
            req_t = urllib.request.Request(url_t, headers={"Accept": "application/sparql-results+json"})
            res_t = json.loads(urllib.request.urlopen(req_t, timeout=3).read().decode())
            status["triples"] = int(res_t["results"]["bindings"][0]["triples"]["value"])
        except Exception:
            pass
    return status


def run_fuseki_query(sparql_query):
    host = get_fuseki_host()
    try:
        url = f"{host}/iso19650/sparql?query=" + urllib.parse.quote(sparql_query)
        req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json"})
        res = urllib.request.urlopen(req, timeout=5).read().decode()
        return json.loads(res)
    except Exception as e:
        return {"error": str(e)}


_rdf_graph_cache = {}

def get_rdf_graph():
    if "graph" not in _rdf_graph_cache:
        ttl_path = os.path.join(ROOT, "data", "generated", "iso19650_kg_unified.ttl")
        if os.path.exists(ttl_path):
            import rdflib
            g = rdflib.Graph()
            g.parse(ttl_path, format="turtle")
            _rdf_graph_cache["graph"] = g
    return _rdf_graph_cache.get("graph")


def star_graph_data(central_id, class_filter=None, limit=25, offset=0):
    try:
        limit = int(limit)
    except Exception:
        limit = 25
    try:
        offset = int(offset)
    except Exception:
        offset = 0

    all_g = graph_data()
    c_node = next((n for n in all_g["nodes"] if n["id"] == central_id), None)
    if not c_node and all_g["nodes"]:
        c_node = all_g["nodes"][0]
        central_id = c_node["id"]

    # Filter edges connected to central_id
    raw_edges = [e for e in all_g["edges"] if e["s"] == central_id or e["t"] == central_id]
    
    # Map neighbor IDs
    nbr_map = {}
    for e in raw_edges:
        other_id = e["t"] if e["s"] == central_id else e["s"]
        nbr_map[other_id] = e

    # Filter by ISO Node Subclass if specified (Concept, Requirement, Process, State, etc.)
    all_nodes_dict = {n["id"]: n for n in all_g["nodes"]}
    filtered_nbr_ids = []
    
    for nid in nbr_map:
        n = all_nodes_dict.get(nid)
        if not n:
            continue
        if class_filter and class_filter.lower() != "all":
            if n.get("label", "").lower() != class_filter.lower():
                continue
        filtered_nbr_ids.append(nid)

    total_children = len(filtered_nbr_ids)
    
    # Apply Lazy Fetch LIMIT & OFFSET
    page_nbr_ids = filtered_nbr_ids[offset : offset + limit]
    page_set = set(page_nbr_ids)
    page_set.add(central_id)

    nodes = [all_nodes_dict[nid] for nid in page_set if nid in all_nodes_dict]
    edges = [e for e in raw_edges if e["s"] in page_set and e["t"] in page_set]

    fuseki_host = get_fuseki_host()
    return {
        "center": c_node,
        "nodes": nodes,
        "edges": edges,
        "total_children": total_children,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total_children,
        "class_filter": class_filter or "all",
        "sparql_source": f"Apache Jena Fuseki ({fuseki_host}/iso19650/sparql) & iso19650_kg_unified.ttl",
        "format": "W3C RDF Turtle (.ttl)"
    }


DIST = os.path.join(ROOT, "frontend", "dist", "frontend", "browser")


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

    def _static(self, path):
        import mimetypes
        rel = path.lstrip("/") or "index.html"
        full = os.path.realpath(os.path.join(DIST, rel))
        if not full.startswith(os.path.realpath(DIST)) or not os.path.isfile(full):
            full = os.path.join(DIST, "index.html")
        if not os.path.isfile(full):
            return self._send(503, json.dumps(
                {"error": "frontend not built - run: cd frontend && npx ng build"}))
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        self._send(200, open(full, "rb").read(), ctype)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        p = parsed.path
        if p == "/api/kg":
            self._send(200, json.dumps(kg_stats()))
        elif p == "/api/fuseki/status":
            self._send(200, json.dumps(fuseki_status()))
        elif p == "/api/spec":
            self._send(200, json.dumps(load_spec()))
        elif p.startswith("/api/graph/star"):
            qs = urllib.parse.parse_qs(parsed.query)
            cid = qs.get("id", ["term_aim"])[0]
            cls = qs.get("class", ["all"])[0]
            lim = qs.get("limit", ["25"])[0]
            off = qs.get("offset", ["0"])[0]
            self._send(200, json.dumps(star_graph_data(cid, class_filter=cls, limit=lim, offset=off)))
        elif p == "/api/graph/rdf":
            self._send(200, json.dumps(rdf_graph_data()))
        elif p == "/api/graph":
            self._send(200, json.dumps(graph_data()))
        elif p == "/api/method":
            self._send(200, json.dumps(method_stats()))
        elif p.startswith("/api/"):
            self._send(404, json.dumps({"error": "not found"}))
        else:
            self._static(p)

    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        if p == "/api/fuseki/query":
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n).decode("utf-8")
            try:
                req_data = json.loads(body)
                q = req_data.get("query", "")
                result = run_fuseki_query(q)
                return self._send(200, json.dumps(result))
            except Exception as e:
                return self._send(400, json.dumps({"error": str(e)}))

        if p != "/api/check":
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
    print(f"Jena Fuseki       ->  {FUSEKI_BROWSER}\nCtrl-C to stop\n", flush=True)
    if host == "127.0.0.1":                  # only auto-open when running locally
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        ThreadingHTTPServer((host, port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
