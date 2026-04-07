from pydantic import BaseModel


class ExtractionResponse(BaseModel):
    success: bool
    record_count: int
    columns_discovered: list[str]
    warnings: list[str]
    file_url: str
