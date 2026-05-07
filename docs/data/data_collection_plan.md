# Mumbai Airport Dataset: Step-by-Step

This project should start with a simple raw data layer for Chhatrapati Shivaji Maharaj International Airport (CSMIA / BOM).

## Final conclusion

Do not start with APIs, embeddings, or FAISS.

Start with 3 raw files:

- `data/raw/food.json`
- `data/raw/shops.json`
- `data/raw/services.json`

These files are your source of truth for the first version of the project.

## What to collect

Collect only basic, useful information for each entity:

- `id`
- `name`
- `terminal`
- `category`
- `description`
- `source_type`
- `source_name`
- `source_query`

Keep it simple first. You can enrich it later.

## Exact steps to follow

1. Search for Mumbai airport food places.
   Use queries like:
   - `Mumbai airport terminal 2 restaurants`
   - `Mumbai airport Starbucks terminal 2`
   - `Mumbai airport food outlets`

2. Search for Mumbai airport shops.
   Use queries like:
   - `Mumbai airport shops`
   - `Mumbai airport duty free`
   - `Mumbai airport terminal 2 retail`

3. Search for Mumbai airport services.
   Use queries like:
   - `Mumbai airport lounges`
   - `Mumbai airport wheelchair assistance`
   - `Mumbai airport medical room`
   - `Mumbai airport forex`

4. Add each result to the collection sheet first.

5. After you have enough rows, copy them into the JSON files.

## How to decide if an item is good enough

Add an item if:

- it clearly belongs to Mumbai airport
- you can identify the terminal or a likely terminal
- you can describe it in one short line

If a source is uncertain, still add it but mark it carefully.

## Source rules

Use these values:

- `source_type`: `official`, `secondary`, or `mock`
- `source_name`: website or source name
- `source_query`: the exact search phrase you used

Examples:

- `official`: airport website
- `secondary`: travel site, news article, maps listing
- `mock`: manually created later for metadata enrichment

## Do not collect these in step 1

Skip these for now:

- exact gates
- walking graph
- flight schedule API data
- embeddings
- vector database
- price inference
- crowd estimation

Those belong to later steps.

## Minimum target

For the first usable dataset, collect:

- 10 food records
- 10 shop records
- 10 service records

That is enough to begin the rest of the pipeline.

## Example workflow for one record

Suppose you find Starbucks in a Mumbai airport source.

1. Add a row to `data/raw/collection_sheet.csv`
2. Add the record to `data/raw/food.json`

Example JSON:

```json
{
  "id": "food_001",
  "name": "Starbucks",
  "terminal": "T2",
  "category": "coffee",
  "description": "Coffee, beverages, and light snacks.",
  "source_type": "secondary",
  "source_name": "travel guide",
  "source_query": "Mumbai airport terminal 2 restaurants"
}
```

## What comes after this

Once the raw data files are ready, the next steps will be:

1. normalize them
2. convert them into RAG records
3. generate search text
4. create embeddings
5. build retrieval

But right now, your only goal is to collect clean raw data.
