# Knowledge Base Implementation

This project now includes a working V1 non-navigation airport knowledge base built from the raw Mumbai Airport Terminal 2 seed files already present in the repository.

## What was added

- a backend knowledge base module under `backend/app/core/knowledge_base/`
- typed schemas for terminal structure, places, flights, offers, raw documents, and RAG chunks
- a repository that reads `data/raw/*.json`, normalizes the records, and writes compiled outputs into the project data folders
- structured retrieval wired into `backend/app/services/rag_service.py`
- orchestrator integration so recommendation prompts now use project knowledge base data instead of hardcoded outlet mocks
- startup compilation so the normalized files are generated automatically when the backend starts
- an official CSMIA Terminal 2 scraper at `backend/scrape_csmia_t2.py`

## Where the code was added

- `backend/app/core/knowledge_base/schemas.py`
  Defines the typed knowledge base models.
- `backend/app/core/knowledge_base/repository.py`
  Loads raw seed data, normalizes it, writes compiled JSON, and provides search helpers.
- `backend/app/services/rag_service.py`
  Connects the backend service layer to the knowledge base repository.
- `backend/app/services/orchestrator.py`
  Uses retrieved place matches and text chunks in the chat prompt.
- `backend/app/main.py`
  Compiles the knowledge base during backend startup.
- `backend/scrape_csmia_t2.py`
  Scrapes official CSMIA Terminal 2 dining, shopping, and lounge data into the raw files.

## Data outputs

The repository now compiles these files from `data/raw/food.json`, `data/raw/shops.json`, and `data/raw/services.json`.

The raw files can be refreshed from the official website with:

```bash
npm run scrape
```

The scraper currently uses these official sources:

- `https://csmia-mumbai.adaniairports.com/en/shop-and-dine/dining`
- `https://csmia-mumbai.adaniairports.com/en/shop-and-dine/shopping`
- `https://csmia-mumbai.adaniairports.com/en/airport-services/lounges`

Compiled outputs:

- `data/airport/terminal_structure.json`
- `data/airport/places.json`
- `data/airport/flights.json`
- `data/airport/offers.json`
- `data/airport/raw_documents.json`
- `data/rag/knowledge_chunks.json`

## Current scope

This version intentionally excludes route graph generation and turn-by-turn navigation.

It supports:

- unified place records for food, shops, and services
- fixed T2 terminal hierarchy
- placeholder flight and offer records until official sources are added
- structured-first retrieval for airport assistant prompts
- RAG chunk generation for later embedding work

## Next steps

1. replace placeholder flights with official ingestion
2. replace placeholder offers with official offer ingestion
3. enrich places with better level, zone, and passenger-side location text
4. add deduplication and confidence scoring
5. add embeddings and vector indexing on top of `data/rag/knowledge_chunks.json`
