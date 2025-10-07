# Cancer Mutation Webtool — Technical Report

## Overview
A local, web-based tool to interpret cancer mutations by integrating scoring algorithms and public databases, with interactive visualization and reporting.

## Requirements Mapping
- Upload: VCF/CSV/JSON (CSV/JSON supported in demo; VCF via cyvcf2 with temp file path).
- Algorithms: SIFT, PolyPhen-2, PROVEAN, MutationAssessor (stubbed); Ensemble: REVEL, MetaLR (derived).
- Databases: COSMIC, ClinVar, MyCancerGenome (stub annotations; ready for API keys if provided).
- Clinical support: Actionable mutation flags and therapy hints (stubbed rules).
- Visualization: Plotly charts via Streamlit; protein structure (py3Dmol planned).
- Reporting: HTML/PDF/Excel export.

## Architecture
- Backend: FastAPI (`app/backend/main.py`) with services: `parsers`, `scoring`, `annotate`, `reports`, `storage`.
- Frontend: Streamlit app (`app/frontend/streamlit_app.py`) communicating with FastAPI.
- Storage: Local JSON per job ID under `data/`.

## Endpoints
- GET `/health` — health check
- POST `/upload` — upload and parse variants
- POST `/analyze` — run scoring, ensemble, annotations, clinical rules
- POST `/report` — export report (html|pdf|xlsx)

## Data Flow
1. User uploads file in UI → `/upload` stores variants (job_id)
2. UI calls `/analyze` with job_id and selected algorithms → results
3. UI renders charts and offers `/report` downloads

## Libraries
- Backend: FastAPI, pydantic, requests, pandas, numpy
- Bio: biopython, cyvcf2 (optional)
- ML: scikit-learn (future/optional)
- Frontend: Streamlit, Plotly
- Reporting: Jinja2, WeasyPrint (PDF), openpyxl (Excel)

## Security & Privacy
- Local-only by default. No external persistence. Optional API integrations require user-provided keys.

## Future Work
- Real API clients for COSMIC/ClinVar/MyCancerGenome, PharmGKB
- Protein 3D visualization overlay (py3Dmol) and PDB mapping
- True AI predictors (AlphaMissense, etc.)
- Auth (OAuth2/JWT) if multi-user needed locally

## Setup & Run
- Install: `pip install -r requirements.txt`
- Run API: `uvicorn app.backend.main:app --reload`
- Run UI: `streamlit run app/frontend/streamlit_app.py`

## Testing
- Plan: pytest suites for parsers, endpoints, and scoring reproducibility.
