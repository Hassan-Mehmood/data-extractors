"""
Write ANX records to an Excel file using openpyxl's write_only mode.

write_only=True streams rows directly to the zip stream without ever
holding the full workbook in memory — safe for very large record sets.
"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import WriteOnlyCell
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet


def write(records: list[dict], columns: list[str], output_path: Path) -> None:
    """
    Write *records* to *output_path* as a single-sheet Excel workbook.

    Parameters
    ----------
    records:
        List of flat dicts produced by the ANX parser.
    columns:
        Ordered list of column names that determines the header row
        and the order in which values are read from each record.
    output_path:
        Absolute path for the output .xlsx file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook(write_only=True)
    ws: Worksheet = wb.create_sheet("Data")

    # Header row — bold
    header_cells = []
    for col_name in columns:
        cell = WriteOnlyCell(ws, value=col_name)
        cell.font = Font(bold=True)
        header_cells.append(cell)
    ws.append(header_cells)

    # Data rows
    for record in records:
        row = [record.get(col, "") for col in columns]
        ws.append(row)

    wb.save(str(output_path))
