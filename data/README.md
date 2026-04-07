
# ANX Sample Files for Testing

This package contains sample ANX (Analyst's Notebook Exchange) files for testing your XML parsing engine.
These files follow the IBM i2 Analyst's Notebook Exchange format specification.

## File Overview

| File | Size | Entities | Relationships | Description |
|------|------|----------|---------------|-------------|
| sample_small.anx | ~12 KB | 10 | 15 | Small network for basic testing |
| sample_medium.anx | ~52 KB | 50 | 80 | Medium fraud investigation network |
| sample_large.anx | ~214 KB | 200 | 350 | Large-scale investigation |
| sample_xlarge.anx | ~594 KB | 500 | 1,000 | Stress test file |

## Entity Types

The sample files contain the following entity types:

- **Person** - Individual subjects/people
- **Company/Organization** - Business entities
- **BankAccount** - Financial accounts
- **Address/Location** - Physical locations
- **Transaction** - Financial transactions
- **Phone** - Phone numbers
- **Email** - Email addresses
- **Vehicle** - Vehicles
- **Document** - Documents (contracts, IDs, etc.)
- **Event** - Events (meetings, conferences, etc.)

## Relationship Types

Common relationship types include:

- Person-to-Person: Friends with, Family member, Colleague, Business partner
- Person-to-Company: Employed by, Owns, Director of, Consultant for
- Company-to-Company: Subsidiary of, Partner with, Merged with, Acquired
- Person-to-BankAccount: Account holder, Authorized user, Beneficiary
- Person-to-Address: Lives at, Works at, Visited
- Transaction relationships: Source of, Destination of, Part of

## ANX File Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Chart xmlns="http://www.i2group.com/Chart/2007">
  <Version>7.0</Version>
  <ChartItemCollection>
    <!-- Entities and Links -->
  </ChartItemCollection>
  <EntityTypeCollection>
    <!-- Entity type definitions -->
  </EntityTypeCollection>
  <LinkTypeCollection>
    <!-- Link type definitions -->
  </LinkTypeCollection>
  <ChartAttributeCollection>
    <!-- Attributes -->
  </ChartAttributeCollection>
</Chart>
```

## Parsing Tips

1. **Entity Parsing**: Look for `<ChartItem>` elements containing `<Entity>` nodes
2. **Link Parsing**: Look for `<ChartItem>` elements containing `<Link>` nodes
3. **Entity IDs**: Found in `<ItemId>` elements
4. **Labels**: Found in `<LabelText>` elements
5. **Dates**: Found in `<DateValue>` elements (ISO 8601 format)
6. **Positions**: X/Y coordinates in `<Position>` elements

## Use Cases

These files are suitable for testing:
- XML parsing engines
- Data extraction tools
- ETL pipelines
- CRM integrations (like HubSpot)
- Network analysis tools
- Link chart generation

## License

These sample files are generated for testing purposes and contain fictitious data.
