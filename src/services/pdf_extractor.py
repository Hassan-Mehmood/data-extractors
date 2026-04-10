from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd


class ScannedPDFError(Exception):
    """Raised when a PDF contains no extractable text (likely scanned/image-based)."""


def extract_tables(pdf_path: Path) -> list[pd.DataFrame]:
    """
    Extract all tables from a text-based PDF using PyMuPDF's built-in table finder.

    Returns a list of DataFrames, one per detected table across all pages.
    Raises ScannedPDFError if no text is found anywhere in the document.
    Raises fitz.FileDataError (or subclass) for corrupt/unreadable files.
    """
    doc = fitz.open(str(pdf_path))

    has_text = any(page.get_text().strip() for page in doc)
    if not has_text:
        raise ScannedPDFError(
            "No extractable text found. This PDF appears to be scanned or image-based. "
            "OCR support is not included in the current version."
        )

    tables: list[pd.DataFrame] = []
    for page in doc:
        finder = page.find_tables()
        for table in finder.tables:
            rows = table.extract()
            if not rows:
                continue
            # First row treated as header; fill empty header cells with positional label
            header = [
                str(cell).strip() if cell else f"Column {i + 1}"
                for i, cell in enumerate(rows[0])
            ]
            data_rows = [
                [str(cell).strip() if cell is not None else "" for cell in row]
                for row in rows[1:]
            ]
            df = pd.DataFrame(data_rows, columns=header)
            # Drop completely empty rows
            df = df[df.apply(lambda r: r.str.strip().any(), axis=1)].reset_index(drop=True)
            if not df.empty:
                tables.append(df)

    return tables
