
"""
Sample ANX Parser for IBM i2 Analyst's Notebook Exchange Files
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Entity:
    item_id: str
    entity_type: str
    label: str
    x: float
    y: float
    description: str
    date: Optional[str] = None

@dataclass
class Link:
    item_id: str
    from_id: str
    to_id: str
    label: str
    description: str

class ANXParser:
    NS = {'anx': 'http://www.i2group.com/Chart/2007'}

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.entities: List[Entity] = []
        self.links: List[Link] = []

    def parse(self):
        """Parse the ANX file and extract entities and links"""
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        # Find all ChartItems
        chart_items = root.find('.//anx:ChartItemCollection', self.NS)
        if chart_items is None:
            chart_items = root.find('.//ChartItemCollection')

        if chart_items is None:
            raise ValueError("Could not find ChartItemCollection")

        for item in chart_items.findall('ChartItem') or chart_items.findall('anx:ChartItem', self.NS):
            self._parse_chart_item(item)

    def _parse_chart_item(self, item):
        """Parse a single ChartItem (Entity or Link)"""
        item_id = self._get_text(item, 'ItemId')

        # Check if it's an Entity
        entity = item.find('anx:Entity', self.NS) or item.find('Entity')
        if entity is not None:
            self._parse_entity(item_id, entity)
            return

        # Check if it's a Link
        link = item.find('anx:Link', self.NS) or item.find('Link')
        if link is not None:
            self._parse_link(item_id, link)

    def _parse_entity(self, item_id: str, entity):
        """Parse an Entity element"""
        entity_type = self._get_text(entity, 'EntityTypeId')
        label = self._get_text(entity, './/LabelText')
        description = self._get_text(entity, 'Description') or ''

        # Get position
        position = entity.find('anx:Position', self.NS) or entity.find('Position')
        x = float(self._get_text(position, 'X') or 0)
        y = float(self._get_text(position, 'Y') or 0)

        # Get date if present
        date_elem = entity.find('anx:Date/anx:DateValue', self.NS) or entity.find('Date/DateValue')
        date = date_elem.text if date_elem is not None else None

        self.entities.append(Entity(
            item_id=item_id,
            entity_type=entity_type,
            label=label,
            x=x,
            y=y,
            description=description,
            date=date
        ))

    def _parse_link(self, item_id: str, link):
        """Parse a Link element"""
        label = self._get_text(link, './/LabelText')
        description = self._get_text(link, 'Description') or ''

        # Get connected entities
        end1 = link.find('anx:End1/anx:EntityId', self.NS) or link.find('End1/EntityId')
        end2 = link.find('anx:End2/anx:EntityId', self.NS) or link.find('End2/EntityId')

        from_id = end1.text if end1 is not None else ''
        to_id = end2.text if end2 is not None else ''

        self.links.append(Link(
            item_id=item_id,
            from_id=from_id,
            to_id=to_id,
            label=label,
            description=description
        ))

    def _get_text(self, parent, xpath: str) -> Optional[str]:
        """Safely get text from an XML element"""
        if parent is None:
            return None
        elem = parent.find(xpath, self.NS) or parent.find(xpath.replace('anx:', ''))
        return elem.text if elem is not None else None

    def to_dataframe(self):
        """Convert entities to pandas DataFrame"""
        import pandas as pd
        data = [{
            'item_id': e.item_id,
            'entity_type': e.entity_type,
            'label': e.label,
            'x': e.x,
            'y': e.y,
            'description': e.description,
            'date': e.date
        } for e in self.entities]
        return pd.DataFrame(data)


# Usage Example
if __name__ == "__main__":
    parser = ANXParser("sample_small.anx")
    parser.parse()

    print(f"Parsed {len(parser.entities)} entities and {len(parser.links)} links")

    # Convert to DataFrame for Excel export
    df = parser.to_dataframe()
    df.to_excel("output.xlsx", index=False)
