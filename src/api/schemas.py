from pydantic import BaseModel


class PDFExtractionResponse(BaseModel):
    filename: str
    download_url: str
    table_count: int
    total_rows: int
