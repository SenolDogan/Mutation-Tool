from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid

from .services.parsers import parse_variant_file
from .services.scoring import run_scoring_algorithms, run_ensemble_scores
from .services.annotate import annotate_with_databases, clinical_actionability
from .services.reports import generate_html_report, generate_pdf_report, generate_excel_report
from .services.storage import LocalJSONStore
from .services.cosmic_client import get_cosmic_client

app = FastAPI(title="Cancer Mutation Webtool API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = LocalJSONStore()


class AnalyzeRequest(BaseModel):
    job_id: Optional[str] = None
    analyses: List[str]
    options: Dict[str, Any] = {}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/upload")
async def upload_variants(file: UploadFile = File(...)) -> Dict[str, Any]:
    try:
        content = await file.read()
        variants = parse_variant_file(file.filename, content)
        job_id = str(uuid.uuid4())
        store.save(job_id, {"filename": file.filename, "variants": variants})
        return {"job_id": job_id, "num_variants": len(variants)}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/analyze")
async def analyze(req: AnalyzeRequest) -> Dict[str, Any]:
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    payload = store.load(req.job_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="job_id not found")

    variants = payload["variants"]
    scores = run_scoring_algorithms(variants, req.analyses, req.options)
    ensemble = run_ensemble_scores(scores)
    annotations = annotate_with_databases(variants)
    clinical = clinical_actionability(annotations)

    results = {
        "variants": variants,
        "scores": scores,
        "ensemble": ensemble,
        "annotations": annotations,
        "clinical": clinical,
    }
    store.save(req.job_id, {**payload, "results": results})
    return {"job_id": req.job_id, **results}


class ReportRequest(BaseModel):
    job_id: str
    format: str = "html"  # html | pdf | xlsx


@app.post("/report")
async def report(req: ReportRequest):
    payload = store.load(req.job_id)
    if payload is None or "results" not in payload:
        raise HTTPException(status_code=404, detail="results not found for job_id")

    results = payload["results"]
    if req.format == "html":
        return {"html": generate_html_report(results)}
    if req.format == "pdf":
        pdf_bytes_b64 = generate_pdf_report(results)
        return {"pdf_base64": pdf_bytes_b64}
    if req.format in {"xlsx", "excel"}:
        xlsx_b64 = generate_excel_report(results)
        return {"excel_base64": xlsx_b64}

    raise HTTPException(status_code=400, detail="Unsupported report format")


class COSMICSearchRequest(BaseModel):
    search_type: str  # "gene", "mutation", "coordinates", "cancer_type"
    query: str
    gene: Optional[str] = None
    chromosome: Optional[str] = None
    position: Optional[int] = None
    ref: Optional[str] = None
    alt: Optional[str] = None


@app.post("/cosmic/search")
async def cosmic_search(req: COSMICSearchRequest):
    cosmic_client = get_cosmic_client()  # Uses mock client for demo
    
    try:
        if req.search_type == "gene":
            result = cosmic_client.get_gene_info(req.query)
        elif req.search_type == "mutation":
            result = cosmic_client.search_mutations(req.gene or req.query, req.query)
        elif req.search_type == "coordinates":
            if not all([req.chromosome, req.position, req.ref, req.alt]):
                raise HTTPException(status_code=400, detail="Missing coordinate parameters")
            result = cosmic_client.search_by_coordinates(req.chromosome, req.position, req.ref, req.alt)
        elif req.search_type == "cancer_type":
            result = cosmic_client.search_cancer_types(req.query)
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        return {"results": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class COSMICMutationRequest(BaseModel):
    cosmic_id: str


@app.post("/cosmic/mutation")
async def cosmic_mutation_details(req: COSMICMutationRequest):
    cosmic_client = get_cosmic_client()
    
    try:
        result = cosmic_client.get_mutation_details(req.cosmic_id)
        return {"mutation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
