from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.core.config import get_settings

# Max characters sent to the model — stays well within gpt-4o-mini's 128k context window
_MAX_CHARS = 80_000

SYSTEM_PROMPT = """\
You are a precise data extraction assistant.
The user will provide a document and describe what data to extract.
You MUST respond with ONLY a valid JSON array of objects — no markdown, no explanation, no code fences.
Each object represents one record. All keys must be strings.
If no matching data is found, return an empty array: []
"""


class LLMExtractionError(Exception):
    """Raised when the LLM returns output that cannot be parsed into a DataFrame."""


def _extract_text(pdf_path: Path) -> str:
    """Extract all text from a PDF, truncated to _MAX_CHARS."""
    doc = fitz.open(str(pdf_path))
    parts: list[str] = []
    total = 0
    for page in doc:
        text = page.get_text()
        remaining = _MAX_CHARS - total
        if remaining <= 0:
            break
        parts.append(text[:remaining])
        total += len(text)
        if total >= _MAX_CHARS:
            break
    return "\n".join(parts)


def extract_with_llm(pdf_path: Path, user_prompt: str) -> pd.DataFrame:
    """
    Extract structured data from a PDF using a LangChain + OpenAI chain.

    The LLM reads the full document text and extracts records based on
    `user_prompt`, returning them as a pandas DataFrame.

    Raises:
        LLMExtractionError: if the model response cannot be parsed as JSON or
            is not a list of dicts.
        ValueError: if OPENAI_API_KEY is not configured.
    """
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to your .env file or environment."
        )

    document_text = _extract_text(pdf_path)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                "Document:\n{document_text}\n\n---\nExtraction instruction: {user_prompt}",
            ),
        ]
    )

    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
    )

    chain = prompt | llm | JsonOutputParser()

    try:
        result = chain.invoke(
            {"document_text": document_text, "user_prompt": user_prompt}
        )
    except Exception as exc:
        raise LLMExtractionError(f"LLM call failed: {exc}") from exc

    if not isinstance(result, list):
        raise LLMExtractionError(
            f"Expected a JSON array from the model, got: {type(result).__name__}"
        )

    if not result:
        return pd.DataFrame()

    if not all(isinstance(row, dict) for row in result):
        raise LLMExtractionError(
            "Model returned a list but not all items are objects (dicts)."
        )

    return pd.DataFrame(result)
