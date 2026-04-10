from pydantic import BaseModel


class PDFExtractionResponse(BaseModel):
    filename: str
    download_url: str
    table_count: int
    total_rows: int


class AIExtractionResponse(BaseModel):
    filename: str
    download_url: str
    row_count: int
    fields: list[str]
