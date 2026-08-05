#!/usr/bin/env python3
"""Upload RDF Turtle Knowledge Graph to Apache Jena Fuseki SPARQL Endpoint.

Usage:  python backend/graphdb/load_fuseki.py [fuseki_url] [dataset_name]
"""
import base64
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

UNIFIED_TTL = "data/generated/iso19650_kg_unified.ttl"
DEFAULT_FUSEKI = os.environ.get("FUSEKI_SERVER", "http://localhost:3030")
DEFAULT_DATASET = "iso19650"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")


def get_auth_header():
    token = base64.b64encode(f"admin:{ADMIN_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def ensure_dataset(server_url, dataset):
    """Create dataset in Fuseki if it does not exist."""
    req = urllib.request.Request(f"{server_url}/$/datasets", headers=get_auth_header())
    try:
        res = urllib.request.urlopen(req).read().decode()
        data = json.loads(res)
        existing = [d.get("ds.name", "").lstrip("/") for d in data.get("datasets", [])]
        if dataset in existing:
            print(f"Dataset '/{dataset}' already exists in Fuseki.")
            return
    except Exception as e:
        print(f"Checking datasets status: {e}")

    # Create dataset
    post_data = urllib.parse.urlencode({"dbName": dataset, "dbType": "tdb2"}).encode()
    req_create = urllib.request.Request(
        f"{server_url}/$/datasets", data=post_data, headers=get_auth_header(), method="POST"
    )
    try:
        urllib.request.urlopen(req_create)
        print(f"Created dataset '/{dataset}' in Fuseki.")
    except Exception as e:
        print(f"Dataset creation note: {e}")


def load_ttl(server_url, dataset):
    """Upload Unified TTL to Fuseki dataset."""
    if not os.path.exists(UNIFIED_TTL):
        print(f"Error: {UNIFIED_TTL} missing. Run export_rdf.py first.")
        sys.exit(1)

    print(f"Uploading {UNIFIED_TTL} to Fuseki dataset '/{dataset}'...")
    with open(UNIFIED_TTL, "rb") as f:
        ttl_bytes = f.read()

    headers = get_auth_header()
    headers["Content-Type"] = "text/turtle; charset=utf-8"

    upload_url = f"{server_url}/{dataset}/data"
    req = urllib.request.Request(upload_url, data=ttl_bytes, headers=headers, method="POST")

    try:
        res = urllib.request.urlopen(req).read().decode()
        res_json = json.loads(res)
        triples = res_json.get("tripleCount", 0)
        print(f"Successfully loaded {triples} RDF Triples into Fuseki dataset '/{dataset}'!")
    except Exception as e:
        print(f"Error loading TTL to Fuseki: {e}")
        sys.exit(1)


def verify_sparql(server_url, dataset):
    """Run verification SPARQL query."""
    sparql = """
    PREFIX iso: <http://example.org/iso19650#>
    SELECT (COUNT(?s) AS ?count) WHERE { ?s a iso:IsoNode . }
    """
    query_url = f"{server_url}/{dataset}/sparql?query=" + urllib.parse.quote(sparql)
    req = urllib.request.Request(query_url, headers={"Accept": "application/sparql-results+json"})

    try:
        res = urllib.request.urlopen(req).read().decode()
        count = json.loads(res)["results"]["bindings"][0]["count"]["value"]
        print(f"Verification: SPARQL Query returned {count} ISO Nodes.")
    except Exception as e:
        print(f"Verification failed: {e}")


def main():
    server_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FUSEKI
    dataset = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_DATASET

    ensure_dataset(server_url, dataset)
    load_ttl(server_url, dataset)
    verify_sparql(server_url, dataset)


if __name__ == "__main__":
    main()
