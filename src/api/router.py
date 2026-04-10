import tempfile
import uuid
from pathlib import Path

import fitz
from fastapi import APIRouter, Form, HTTPException, Request, UploadFile

from src.api.schemas import AIExtractionResponse, PDFExtractionResponse
from src.core.config import get_settings
from src.services.excel_exporter import export_to_excel
from src.services.llm_extractor import LLMExtractionError, extract_with_llm
from src.services.pdf_extractor import ScannedPDFError, extract_tables

router = APIRouter(prefix="/api")


@router.post("/pdf/extract", response_model=PDFExtractionResponse)
async def extract_pdf(request: Request, file: UploadFile) -> PDFExtractionResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    settings = get_settings()
    exports_dir = Path(settings.EXPORTS_DIR)

    # Write upload to a temp file so PyMuPDF can open it by path
    suffix = Path(file.filename or "upload").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        tables = extract_tables(tmp_path)
    except ScannedPDFError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except fitz.FileDataError as exc:
        raise HTTPException(
            status_code=400, detail="Could not read PDF — file may be corrupt."
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Unexpected extraction error: {exc}"
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    if not tables:
        raise HTTPException(
            status_code=422,
            detail="No tables were detected in this PDF. The document may contain only plain text or non-standard layout.",
        )

    stem = Path(file.filename or "output").stem
    out_name = f"{stem}_{uuid.uuid4().hex[:8]}.xlsx"
    out_path = exports_dir / out_name
    export_to_excel(tables, out_path)

    base_url = str(request.base_url).rstrip("/")
    download_url = f"{base_url}/exports/{out_name}"
    total_rows = sum(len(df) for df in tables)

    return PDFExtractionResponse(
        filename=out_name,
        download_url=download_url,
        table_count=len(tables),
        total_rows=total_rows,
    )


@router.post("/pdf/extract-ai", response_model=AIExtractionResponse)
async def extract_pdf_with_ai(
    request: Request,
    file: UploadFile,
    prompt: str = Form(...),
) -> AIExtractionResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Extraction prompt must not be empty.")

    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured on the server.",
        )

    exports_dir = Path(settings.EXPORTS_DIR)

    suffix = Path(file.filename or "upload").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        df = extract_with_llm(tmp_path, prompt)
    except LLMExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Unexpected AI extraction error: {exc}"
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    if df.empty:
        raise HTTPException(
            status_code=422,
            detail="The model found no matching data for the given prompt.",
        )

    stem = Path(file.filename or "output").stem
    out_name = f"{stem}_ai_{uuid.uuid4().hex[:8]}.xlsx"
    out_path = exports_dir / out_name
    export_to_excel([df], out_path)

    base_url = str(request.base_url).rstrip("/")
    download_url = f"{base_url}/exports/{out_name}"

    return AIExtractionResponse(
        filename=out_name,
        download_url=download_url,
        row_count=len(df),
        fields=list(df.columns),
    )
