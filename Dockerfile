# ISO 19650 Knowledge Graph & PdM readiness toolchain
# Zero Python dependencies (stdlib only); poppler-utils provides pdftotext/pdftoppm
# for the tools that read the source standards (evaluate_kg, draft_extractor).
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends poppler-utils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# The web UI binds 127.0.0.1 by default; inside a container it must be reachable.
ENV HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/kg',timeout=2)" || exit 1

CMD ["python3", "tmp/serve.py", "8000"]
