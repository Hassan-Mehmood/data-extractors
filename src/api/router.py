import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.api.schemas import ExtractionResponse, QueryResponse
from src.core.config import get_settings
from src.services import ai_filter, anx_parser, excel_writer

settings = get_settings()

router = APIRouter(prefix="/api", tags=["extraction"])

_ALLOWED_SUFFIXES = {".anx", ".xml"}
_MAX_UPLOAD_BYTES = 512 * 1024 * 1024  # 512 MB


@router.post(
    "/upload",
    response_model=ExtractionResponse,
    summary="Upload an ANX file and extract records to Excel",
)
async def upload_anx(file: UploadFile) -> JSONResponse:
    # Basic validation
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type {suffix!r}. Expected .anx or .xml.",
        )

    exports_dir = Path(settings.EXPORTS_DIR)

    # Stream upload into a named temp file so lxml can seek/read it
    with tempfile.NamedTemporaryFile(suffix=".anx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        bytes_written = 0
        while chunk := await file.read(1024 * 256):  # 256 KB chunks
            bytes_written += len(chunk)
            if bytes_written > _MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="File exceeds the 512 MB upload limit.",
                )
            tmp.write(chunk)

    try:
        result = anx_parser.parse(tmp_path)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422, detail=f"Failed to parse ANX file: {exc}"
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    output_filename = f"{uuid.uuid4()}.xlsx"
    output_path = exports_dir / output_filename

    try:
        excel_writer.write(result.records, result.columns, output_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to write Excel file: {exc}"
        ) from exc

    return JSONResponse(
        content=ExtractionResponse(
            success=True,
            record_count=len(result.records),
            columns_discovered=result.columns,
            warnings=result.warnings,
            file_url=f"/exports/{output_filename}",
        ).model_dump()
    )


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Upload an ANX file and filter records using a natural-language prompt",
)
async def query_anx(
    file: UploadFile,
    prompt: str = Form(
        ..., description="Natural-language description of which records to extract"
    ),
) -> JSONResponse:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured. Set it in your .env file.",
        )

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type {suffix!r}. Expected .anx or .xml.",
        )

    exports_dir = Path(settings.EXPORTS_DIR)

    with tempfile.NamedTemporaryFile(suffix=".anx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        bytes_written = 0
        while chunk := await file.read(1024 * 256):
            bytes_written += len(chunk)
            if bytes_written > _MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="File exceeds the 512 MB upload limit.",
                )
            tmp.write(chunk)

    try:
        result = anx_parser.parse(tmp_path)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422, detail=f"Failed to parse ANX file: {exc}"
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    try:
        matched = ai_filter.filter_records(result.records, prompt, settings)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"AI filtering failed: {exc}"
        ) from exc

    output_filename = f"{uuid.uuid4()}.xlsx"
    output_path = exports_dir / output_filename

    try:
        excel_writer.write(matched, result.columns, output_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to write Excel file: {exc}"
        ) from exc

    return JSONResponse(
        content=QueryResponse(
            success=True,
            matched_count=len(matched),
            total_count=len(result.records),
            columns_discovered=result.columns,
            warnings=result.warnings,
            file_url=f"/exports/{output_filename}",
        ).model_dump()
    )
