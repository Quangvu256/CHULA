#!/usr/bin/env python3
"""API backend + static host for the Angular frontend.

    python3 backend/serve.py [port]        # http://localhost:8000

Endpoints: /api/kg /api/spec /api/graph /api/method /api/check (POST, raw body
+ X-Filename). Everything else serves frontend/dist (SPA fallback to index.html).
The audit logic is imported from check_ifc_pdm so the CLI and the web UI cannot
disagree. Stdlib only; HOST=0.0.0.0 for containers.
"""
import json, os, sys, tempfile, threading, webbrowser, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from check_ifc_pdm import run_check, load_spec          # noqa: E402

NEO4J_BROWSER = os.environ.get("NEO4J_BROWSER", "http://192.168.110.146:7474")
KG_FILES = ["data/iso19650-1_extraction_v4.json", "data/iso19650-2_extraction_v1.json",
            "data/iso19650-3_extraction_v1.2.json", "data/iso19650-4_extraction_v1.json",
            "data/iso19650-5_extraction_v1.json", "data/iso19650-6_extraction_v2.json"]
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
        """Serve the built Angular app. Unknown non-API paths fall back to
        index.html (SPA). Traversal is blocked by resolving inside DIST."""
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
        p = urllib.parse.urlparse(self.path).path
        if p == "/api/kg":
            self._send(200, json.dumps(kg_stats()))
        elif p == "/api/spec":
            self._send(200, json.dumps(load_spec()))
        elif p == "/api/graph":
            self._send(200, json.dumps(graph_data()))
        elif p == "/api/method":
            self._send(200, json.dumps(method_stats()))
        elif p.startswith("/api/"):
            self._send(404, json.dumps({"error": "not found"}))
        else:
            self._static(p)

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
