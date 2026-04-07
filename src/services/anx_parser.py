"""
Memory-efficient ANX parser using lxml iterparse.

Streams ChartItem elements from IBM i2 ANX files one at a time,
clearing each from the tree after processing to keep memory flat.
"""

from collections.abc import Generator
from pathlib import Path

from lxml import etree

NS = "http://www.i2group.com/Chart/2007"

# Tags we care about, fully qualified
_CHART_ITEM_TAG = f"{{{NS}}}ChartItem"
_ENTITY_TAG = f"{{{NS}}}Entity"
_LINK_TAG = f"{{{NS}}}Link"


def _text(elem: etree._Element, local_tag: str) -> str:
    """Return .text of the first child matching local_tag (with NS), or ''."""
    child = elem.find(f"{{{NS}}}{local_tag}")
    if child is not None and child.text:
        return child.text.strip()
    return ""


def _nested_text(elem: etree._Element, *local_tags: str) -> str:
    """Walk a chain of local_tags and return the deepest element's text."""
    current = elem
    for tag in local_tags:
        current = current.find(f"{{{NS}}}{tag}")
        if current is None:
            return ""
    return current.text.strip() if current.text else ""


def _parse_entity(item_id: str, entity: etree._Element) -> dict:
    position = entity.find(f"{{{NS}}}Position")
    x = _text(position, "X") if position is not None else ""
    y = _text(position, "Y") if position is not None else ""

    date_val = entity.find(f".//{{{NS}}}DateValue")

    return {
        "record_type": "Entity",
        "item_id": item_id,
        "entity_type": _text(entity, "EntityTypeId"),
        "label": _nested_text(entity, "Label", "LabelText"),
        "x": x,
        "y": y,
        "description": _text(entity, "Description"),
        "date": date_val.text.strip() if date_val is not None and date_val.text else "",
    }


def _parse_link(item_id: str, link: etree._Element) -> dict:
    end1 = link.find(f"{{{NS}}}End1")
    end2 = link.find(f"{{{NS}}}End2")
    from_id = _text(end1, "EntityId") if end1 is not None else ""
    to_id = _text(end2, "EntityId") if end2 is not None else ""

    return {
        "record_type": "Link",
        "item_id": item_id,
        "link_type": _text(link, "LinkTypeId"),
        "label": _nested_text(link, "Label", "LabelText"),
        "from_id": from_id,
        "to_id": to_id,
        "description": _text(link, "Description"),
    }


class ParseResult:
    __slots__ = ("records", "columns", "warnings")

    def __init__(
        self,
        records: list[dict],
        columns: list[str],
        warnings: list[str],
    ) -> None:
        self.records = records
        self.columns = columns
        self.warnings = warnings


def parse(file_path: Path) -> ParseResult:
    """
    Stream-parse an ANX file and return all records, discovered columns,
    and any warnings encountered.
    """
    records: list[dict] = []
    warnings: list[str] = []
    all_keys: dict[str, None] = {}  # ordered set via insertion-ordered dict

    context = etree.iterparse(
        str(file_path),
        events=("end",),
        tag=_CHART_ITEM_TAG,
        recover=True,
    )

    for _event, elem in context:
        item_id_elem = elem.find(f"{{{NS}}}ItemId")
        item_id = item_id_elem.text.strip() if item_id_elem is not None and item_id_elem.text else ""

        entity = elem.find(_ENTITY_TAG)
        link = elem.find(_LINK_TAG)

        if entity is not None:
            record = _parse_entity(item_id, entity)
            label = record.get("label", "")
            if not label:
                warnings.append(f"Entity {item_id!r} has no label text")
        elif link is not None:
            record = _parse_link(item_id, link)
        else:
            warnings.append(f"ChartItem {item_id!r} contains neither Entity nor Link — skipped")
            elem.clear()
            continue

        records.append(record)
        for key in record:
            all_keys[key] = None

        # Free memory — critical for large files
        elem.clear()
        # Also discard preceding siblings to free the root's child list
        parent = elem.getparent()
        if parent is not None:
            parent.remove(elem)

    # Canonical column order: shared Entity+Link fields first, then type-specific
    preferred_order = [
        "record_type", "item_id", "entity_type", "link_type",
        "label", "from_id", "to_id", "x", "y", "description", "date",
    ]
    columns = [c for c in preferred_order if c in all_keys] + [
        c for c in all_keys if c not in preferred_order
    ]

    return ParseResult(records=records, columns=columns, warnings=warnings)


def iter_records(file_path: Path) -> Generator[dict, None, None]:
    """Yield records one at a time without accumulating them in memory."""
    context = etree.iterparse(
        str(file_path),
        events=("end",),
        tag=_CHART_ITEM_TAG,
        recover=True,
    )
    for _event, elem in context:
        item_id_elem = elem.find(f"{{{NS}}}ItemId")
        item_id = item_id_elem.text.strip() if item_id_elem is not None and item_id_elem.text else ""

        entity = elem.find(_ENTITY_TAG)
        link = elem.find(_LINK_TAG)

        if entity is not None:
            yield _parse_entity(item_id, entity)
        elif link is not None:
            yield _parse_link(item_id, link)

        elem.clear()
        parent = elem.getparent()
        if parent is not None:
            parent.remove(elem)
