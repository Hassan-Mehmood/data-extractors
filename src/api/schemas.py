from pydantic import BaseModel


class ExtractionResponse(BaseModel):
    success: bool
    record_count: int
    columns_discovered: list[str]
    warnings: list[str]
    file_url: str


class QueryResponse(BaseModel):
    success: bool
    matched_count: int
    total_count: int
    columns_discovered: list[str]
    warnings: list[str]
    file_url: str
