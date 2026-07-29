# ---- Stage 1: build the Angular frontend --------------------------------------
FROM node:22-alpine AS fe
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npx ng build

# ---- Stage 2: Python runtime (stdlib only) ------------------------------------
# poppler-utils provides pdftotext/pdftoppm for the tools that read the source
# standards (evaluate_kg, draft_extractor); the web app itself needs nothing.
FROM python:3.12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends poppler-utils \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/ backend/
COPY docs/ docs/
COPY data/ data/
COPY --from=fe /fe/dist/frontend/browser frontend/dist/frontend/browser

ENV HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/kg',timeout=2)" || exit 1
CMD ["python3", "backend/api/serve.py", "8000"]
